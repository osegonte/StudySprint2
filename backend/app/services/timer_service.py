# backend/app/services/timer_service.py
"""Timer & Analytics Service for Stage 3.4"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from fastapi import HTTPException, status

from app.models import (
    StudySession, PageTime, PomodoroSession, ReadingSpeed, 
    TimeEstimate, UserStatistic, PDF, Topic
)
from app.schemas import (
    StudySessionCreate, StudySessionUpdate, SessionActivityUpdate,
    PageTimeCreate, PageTimeUpdate, PomodoroSessionCreate, 
    ReadingSpeedCreate, TimeEstimateCreate, StudyAnalyticsRequest
)
from app.utils.crud_router import CRUDService
from studysprint_db.models.user import User


class TimerService(CRUDService):
    """Comprehensive timer and analytics service"""
    
    def __init__(self):
        super().__init__(StudySession)
    
    # ============================================================================
    # STUDY SESSION MANAGEMENT
    # ============================================================================
    
    def start_session(
        self, 
        db: Session, 
        session_data: StudySessionCreate, 
        user_id: str
    ) -> StudySession:
        """Start a new study session"""
        
        # Verify PDF and Topic ownership
        pdf = db.query(PDF).filter(
            PDF.id == session_data.pdf_id,
            PDF.user_id == user_id,
            PDF.is_deleted == False
        ).first()
        
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        # End any existing active sessions for this user
        self._end_existing_sessions(db, user_id)
        
        # Create new session
        session = StudySession(
            user_id=user_id,
            pdf_id=session_data.pdf_id,
            topic_id=session_data.topic_id,
            session_type=session_data.session_type,
            planned_cycles=session_data.planned_cycles,
            notes=session_data.notes,
            start_time=datetime.now(timezone.utc),
            is_active=True
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    def pause_session(self, db: Session, session_id: UUID, user_id: str, reason: str = None) -> StudySession:
        """Pause an active study session"""
        session = self._get_user_session(db, session_id, user_id)
        
        if not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not active"
            )
        
        if session.is_paused:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is already paused"
            )
        
        session.is_paused = True
        session.pause_count += 1
        
        # Update timing
        self._update_session_timing(session)
        
        if reason:
            if not session.metadata:
                session.metadata = {}
            session.metadata.setdefault('pause_reasons', []).append({
                'reason': reason,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        db.commit()
        db.refresh(session)
        
        return session
    
    def resume_session(self, db: Session, session_id: UUID, user_id: str) -> StudySession:
        """Resume a paused study session"""
        session = self._get_user_session(db, session_id, user_id)
        
        if not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not active"
            )
        
        if not session.is_paused:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not paused"
            )
        
        session.is_paused = False
        
        # Record resume time
        if not session.metadata:
            session.metadata = {}
        session.metadata.setdefault('resume_times', []).append(
            datetime.now(timezone.utc).isoformat()
        )
        
        db.commit()
        db.refresh(session)
        
        return session
    
    def end_session(
        self, 
        db: Session, 
        session_id: UUID, 
        user_id: str, 
        session_rating: int = None,
        notes: str = None
    ) -> StudySession:
        """End a study session and calculate final metrics"""
        session = self._get_user_session(db, session_id, user_id)
        
        if not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not active"
            )
        
        # Update session details
        if session_rating:
            session.session_rating = session_rating
        if notes:
            session.notes = notes
        
        # End session and calculate metrics
        session.end_session()
        
        # Update PDF statistics
        pdf = db.query(PDF).filter(PDF.id == session.pdf_id).first()
        if pdf:
            pdf.actual_read_time += session.active_minutes
            pdf.view_count += 1
            pdf.last_viewed_at = datetime.now(timezone.utc)
        
        # Update topic statistics
        topic = db.query(Topic).filter(Topic.id == session.topic_id).first()
        if topic:
            topic.total_study_time += session.active_minutes
            topic.last_studied_at = datetime.now(timezone.utc)
        
        # Create reading speed entry
        self._create_reading_speed_entry(db, session)
        
        # Update user statistics
        self._update_user_statistics(db, user_id, session)
        
        db.commit()
        db.refresh(session)
        
        return session
    
    def update_session_activity(
        self, 
        db: Session, 
        session_id: UUID, 
        user_id: str, 
        activity: SessionActivityUpdate
    ) -> StudySession:
        """Update session activity metrics"""
        session = self._get_user_session(db, session_id, user_id)
        
        if not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not active"
            )
        
        # Update activity counts
        update_data = activity.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(session, field):
                setattr(session, field, max(getattr(session, field), value))
        
        # Update timing
        self._update_session_timing(session)
        
        db.commit()
        db.refresh(session)
        
        return session
    
    def get_active_session(self, db: Session, user_id: str) -> Optional[StudySession]:
        """Get current active session for user"""
        return db.query(StudySession).filter(
            StudySession.user_id == user_id,
            StudySession.is_active == True,
            StudySession.is_deleted == False
        ).first()
    
    def get_session_history(
        self, 
        db: Session, 
        user_id: str, 
        limit: int = 50,
        days: int = 30
    ) -> List[StudySession]:
        """Get user's session history"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        return db.query(StudySession).filter(
            StudySession.user_id == user_id,
            StudySession.start_time >= start_date,
            StudySession.is_deleted == False
        ).order_by(desc(StudySession.start_time)).limit(limit).all()
    
    # ============================================================================
    # PAGE-LEVEL TIMING
    # ============================================================================
    
    def start_page_timer(
        self, 
        db: Session, 
        page_data: PageTimeCreate, 
        user_id: str
    ) -> PageTime:
        """Start timing for a specific page"""
        
        # Verify session ownership
        session = self._get_user_session(db, page_data.session_id, user_id)
        
        # End any existing page timing for this session
        existing_page_time = db.query(PageTime).filter(
            PageTime.session_id == page_data.session_id,
            PageTime.end_time.is_(None)
        ).first()
        
        if existing_page_time:
            existing_page_time.end_page_timing()
        
        # Create new page timing
        page_time = PageTime(
            session_id=page_data.session_id,
            pdf_id=page_data.pdf_id,
            page_number=page_data.page_number,
            estimated_words=page_data.estimated_words,
            start_time=datetime.now(timezone.utc)
        )
        
        db.add(page_time)
        db.commit()
        db.refresh(page_time)
        
        return page_time
    
    def end_page_timer(
        self, 
        db: Session, 
        page_time_id: UUID, 
        user_id: str
    ) -> PageTime:
        """End timing for a specific page"""
        page_time = db.query(PageTime).filter(
            PageTime.id == page_time_id,
            PageTime.end_time.is_(None)
        ).join(StudySession).filter(
            StudySession.user_id == user_id
        ).first()
        
        if not page_time:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active page timer not found"
            )
        
        page_time.end_page_timing()
        
        db.commit()
        db.refresh(page_time)
        
        return page_time
    
    def update_page_activity(
        self, 
        db: Session, 
        page_time_id: UUID, 
        user_id: str,
        activity: PageTimeUpdate
    ) -> PageTime:
        """Update page activity metrics"""
        page_time = db.query(PageTime).filter(
            PageTime.id == page_time_id
        ).join(StudySession).filter(
            StudySession.user_id == user_id
        ).first()
        
        if not page_time:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page timer not found"
            )
        
        # Update activity metrics
        update_data = activity.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(page_time, field):
                current_value = getattr(page_time, field)
                setattr(page_time, field, max(current_value, value))
        
        # Update total activity count
        page_time.activity_count = (
            page_time.click_count + 
            page_time.scroll_count + 
            page_time.zoom_changes
        )
        
        db.commit()
        db.refresh(page_time)
        
        return page_time
    
    # ============================================================================
    # POMODORO INTEGRATION
    # ============================================================================
    
    def start_pomodoro_cycle(
        self, 
        db: Session, 
        pomodoro_data: PomodoroSessionCreate, 
        user_id: str
    ) -> PomodoroSession:
        """Start a new Pomodoro cycle"""
        
        # Verify study session ownership
        session = self._get_user_session(db, pomodoro_data.study_session_id, user_id)
        
        # Create Pomodoro cycle
        pomodoro = PomodoroSession(
            study_session_id=pomodoro_data.study_session_id,
            cycle_number=pomodoro_data.cycle_number,
            cycle_type=pomodoro_data.cycle_type,
            planned_duration_minutes=pomodoro_data.planned_duration_minutes,
            started_at=datetime.now(timezone.utc)
        )
        
        db.add(pomodoro)
        db.commit()
        db.refresh(pomodoro)
        
        return pomodoro
    
    def complete_pomodoro_cycle(
        self, 
        db: Session, 
        pomodoro_id: UUID, 
        user_id: str,
        effectiveness_rating: int = None,
        interruptions: int = 0
    ) -> PomodoroSession:
        """Complete a Pomodoro cycle"""
        pomodoro = db.query(PomodoroSession).filter(
            PomodoroSession.id == pomodoro_id,
            PomodoroSession.completed == False
        ).join(StudySession).filter(
            StudySession.user_id == user_id
        ).first()
        
        if not pomodoro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active Pomodoro cycle not found"
            )
        
        pomodoro.interruptions = interruptions
        pomodoro.complete_cycle(effectiveness_rating)
        
        # Update study session
        study_session = db.query(StudySession).filter(
            StudySession.id == pomodoro.study_session_id
        ).first()
        
        if study_session:
            study_session.pomodoro_cycles += 1
            study_session.xp_earned += pomodoro.xp_earned
        
        db.commit()
        db.refresh(pomodoro)
        
        return pomodoro
    
    # ============================================================================
    # SMART TIME ESTIMATION
    # ============================================================================
    
    def create_time_estimate(
        self, 
        db: Session, 
        estimate_data: TimeEstimateCreate, 
        user_id: str
    ) -> TimeEstimate:
        """Create a smart time estimate"""
        
        # Calculate confidence score based on historical data
        confidence_score = self._calculate_confidence_score(
            db, user_id, estimate_data.estimate_type, 
            estimate_data.pdf_id, estimate_data.topic_id
        )
        
        # Create estimate
        estimate = TimeEstimate(
            user_id=user_id,
            pdf_id=estimate_data.pdf_id,
            topic_id=estimate_data.topic_id,
            estimate_type=estimate_data.estimate_type,
            estimated_minutes=estimate_data.estimated_minutes,
            estimated_sessions=estimate_data.estimated_sessions,
            confidence_level=estimate_data.confidence_level,
            confidence_score=confidence_score,
            factors_used=estimate_data.factors_used,
            valid_until=datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        db.add(estimate)
        db.commit()
        db.refresh(estimate)
        
        return estimate
    
    def get_smart_estimates(
        self, 
        db: Session, 
        user_id: str, 
        pdf_id: UUID = None,
        topic_id: UUID = None
    ) -> List[TimeEstimate]:
        """Get smart time estimates for user"""
        query = db.query(TimeEstimate).filter(
            TimeEstimate.user_id == user_id,
            TimeEstimate.is_active == True,
            or_(
                TimeEstimate.valid_until.is_(None),
                TimeEstimate.valid_until > datetime.now(timezone.utc)
            )
        )
        
        if pdf_id:
            query = query.filter(TimeEstimate.pdf_id == pdf_id)
        if topic_id:
            query = query.filter(TimeEstimate.topic_id == topic_id)
        
        return query.order_by(desc(TimeEstimate.created_at)).all()
    
    def calculate_reading_completion_estimate(
        self, 
        db: Session, 
        pdf_id: UUID, 
        user_id: str
    ) -> Dict[str, Any]:
        """Calculate smart completion estimate for PDF"""
        
        # Get PDF details
        pdf = db.query(PDF).filter(
            PDF.id == pdf_id,
            PDF.user_id == user_id,
            PDF.is_deleted == False
        ).first()
        
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        # Get user's reading speed history
        avg_reading_speed = db.query(func.avg(ReadingSpeed.pages_per_minute)).filter(
            ReadingSpeed.user_id == user_id,
            ReadingSpeed.content_type == 'text',
            ReadingSpeed.difficulty_level == pdf.difficulty_rating
        ).scalar() or 0.5  # Default 0.5 pages per minute
        
        # Calculate remaining pages
        remaining_pages = max(0, pdf.total_pages - pdf.current_page + 1)
        
        # Estimate time
        estimated_minutes = int(remaining_pages / avg_reading_speed)
        
        # Adjust for difficulty
        difficulty_multiplier = {1: 0.8, 2: 0.9, 3: 1.0, 4: 1.2, 5: 1.5}
        estimated_minutes = int(estimated_minutes * difficulty_multiplier.get(pdf.difficulty_rating, 1.0))
        
        # Calculate confidence
        session_count = db.query(func.count(StudySession.id)).filter(
            StudySession.user_id == user_id,
            StudySession.pdf_id == pdf_id
        ).scalar() or 0
        
        confidence_level = "high" if session_count >= 3 else "medium" if session_count >= 1 else "low"
        
        return {
            "pdf_id": str(pdf_id),
            "remaining_pages": remaining_pages,
            "estimated_minutes": estimated_minutes,
            "estimated_hours": round(estimated_minutes / 60, 2),
            "confidence_level": confidence_level,
            "avg_reading_speed": float(avg_reading_speed),
            "based_on_sessions": session_count,
            "difficulty_adjustment": difficulty_multiplier.get(pdf.difficulty_rating, 1.0)
        }
    
    # ============================================================================
    # ANALYTICS AND INSIGHTS
    # ============================================================================
    
    def get_study_analytics(
        self, 
        db: Session, 
        user_id: str, 
        request: StudyAnalyticsRequest
    ) -> Dict[str, Any]:
        """Get comprehensive study analytics"""
        
        # Date range
        end_date = request.end_date or datetime.now(timezone.utc)
        start_date = request.start_date or end_date - timedelta(days=30)
        
        # Base query
        query = db.query(StudySession).filter(
            StudySession.user_id == user_id,
            StudySession.start_time >= start_date,
            StudySession.start_time <= end_date,
            StudySession.is_deleted == False
        )
        
        # Apply filters
        if request.pdf_ids:
            query = query.filter(StudySession.pdf_id.in_(request.pdf_ids))
        if request.topic_ids:
            query = query.filter(StudySession.topic_id.in_(request.topic_ids))
        
        sessions = query.all()
        
        # Calculate overview metrics
        overview = self._calculate_overview_metrics(sessions)
        
        # Calculate trends
        trends = self._calculate_trends(sessions, request.granularity)
        
        # Calculate performance metrics
        performance = self._calculate_performance_metrics(sessions)
        
        # Calculate reading speed metrics
        reading_speed = self._calculate_reading_speed_metrics(db, user_id, start_date, end_date)
        
        # Calculate focus patterns
        focus_patterns = self._calculate_focus_patterns(sessions)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(sessions, performance, focus_patterns)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "overview": overview,
            "trends": trends,
            "performance": performance,
            "reading_speed": reading_speed,
            "focus_patterns": focus_patterns,
            "recommendations": recommendations
        }
    
    def get_reading_patterns(self, db: Session, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze reading patterns and optimal study times"""
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get reading speed data
        reading_speeds = db.query(ReadingSpeed).filter(
            ReadingSpeed.user_id == user_id,
            ReadingSpeed.created_at >= start_date
        ).all()
        
        # Get study sessions
        sessions = db.query(StudySession).filter(
            StudySession.user_id == user_id,
            StudySession.start_time >= start_date,
            StudySession.is_deleted == False
        ).all()
        
        # Analyze patterns
        hourly_performance = self._analyze_hourly_performance(sessions)
        daily_performance = self._analyze_daily_performance(sessions)
        reading_trends = self._analyze_reading_speed_trends(reading_speeds)
        
        return {
            "optimal_study_hours": hourly_performance["best_hours"],
            "best_performing_days": daily_performance["best_days"],
            "reading_speed_trends": reading_trends,
            "focus_score_trends": self._analyze_focus_trends(sessions),
            "productivity_trends": self._analyze_productivity_trends(sessions),
            "content_type_preferences": self._analyze_content_preferences(reading_speeds),
            "difficulty_performance": self._analyze_difficulty_performance(sessions)
        }
    
    # ============================================================================
    # PRIVATE HELPER METHODS
    # ============================================================================
    
    def _get_user_session(self, db: Session, session_id: UUID, user_id: str) -> StudySession:
        """Get session with user ownership verification"""
        session = db.query(StudySession).filter(
            StudySession.id == session_id,
            StudySession.user_id == user_id,
            StudySession.is_deleted == False
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study session not found"
            )
        
        return session
    
    def _end_existing_sessions(self, db: Session, user_id: str) -> None:
        """End any existing active sessions for user"""
        active_sessions = db.query(StudySession).filter(
            StudySession.user_id == user_id,
            StudySession.is_active == True,
            StudySession.is_deleted == False
        ).all()
        
        for session in active_sessions:
            session.end_session()
    
    def _update_session_timing(self, session: StudySession) -> None:
        """Update session timing metrics"""
        if session.start_time:
            current_time = datetime.now(timezone.utc)
            delta = current_time - session.start_time
            session.total_minutes = int(delta.total_seconds() / 60)
            
            # Calculate active vs idle time (simplified)
            if not session.is_paused:
                session.active_minutes = min(session.total_minutes, session.active_minutes + 1)
            else:
                session.idle_minutes = session.total_minutes - session.active_minutes
    
    def _create_reading_speed_entry(self, db: Session, session: StudySession) -> None:
        """Create reading speed entry from session data"""
        if session.pages_visited == 0 or session.active_minutes == 0:
            return
        
        pages_per_minute = session.pages_visited / session.active_minutes
        
        # Estimate words (approximate)
        words_per_minute = pages_per_minute * 250  # Assume 250 words per page
        
        reading_speed = ReadingSpeed(
            user_id=session.user_id,
            pdf_id=session.pdf_id,
            topic_id=session.topic_id,
            session_id=session.id,
            pages_per_minute=pages_per_minute,
            words_per_minute=words_per_minute,
            characters_per_minute=words_per_minute * 5,  # Estimate
            content_type='mixed',
            difficulty_level=3,  # Default
            estimated_words=session.pages_visited * 250,
            time_of_day=session.start_time.hour,
            day_of_week=session.start_time.weekday(),
            session_duration=session.active_minutes
        )
        
        db.add(reading_speed)
    
    def _update_user_statistics(self, db: Session, user_id: str, session: StudySession) -> None:
        """Update user statistics with session data"""
        today = datetime.now(timezone.utc).date()
        
        # Get or create daily statistics
        daily_stats = db.query(UserStatistic).filter(
            UserStatistic.user_id == user_id,
            UserStatistic.stat_type == 'daily',
            func.date(UserStatistic.stat_date) == today
        ).first()
        
        if not daily_stats:
            daily_stats = UserStatistic(
                user_id=user_id,
                stat_type='daily',
                stat_date=datetime.now(timezone.utc)
            )
            db.add(daily_stats)
        
        # Update statistics
        daily_stats.total_study_minutes += session.active_minutes
        daily_stats.total_active_minutes += session.active_minutes
        daily_stats.total_sessions += 1
        daily_stats.pages_read += session.pages_visited
        daily_stats.pomodoro_cycles_completed += session.pomodoro_cycles
        daily_stats.xp_earned += session.xp_earned
        
        # Update averages
        if daily_stats.total_sessions > 0:
            daily_stats.average_focus_score = (
                daily_stats.average_focus_score * (daily_stats.total_sessions - 1) + 
                session.focus_score
            ) / daily_stats.total_sessions
            
            daily_stats.average_productivity_score = (
                daily_stats.average_productivity_score * (daily_stats.total_sessions - 1) + 
                session.productivity_score
            ) / daily_stats.total_sessions
    
    def _calculate_overview_metrics(self, sessions: List[StudySession]) -> Dict[str, Any]:
        """Calculate overview metrics from sessions"""
        if not sessions:
            return {
                "total_sessions": 0,
                "total_study_minutes": 0,
                "total_active_minutes": 0,
                "average_session_length": 0,
                "average_focus_score": 0.0,
                "average_productivity_score": 0.0,
                "total_pages_visited": 0,
                "total_pomodoro_cycles": 0
            }
        
        return {
            "total_sessions": len(sessions),
            "total_study_minutes": sum(s.total_minutes for s in sessions),
            "total_active_minutes": sum(s.active_minutes for s in sessions),
            "average_session_length": sum(s.total_minutes for s in sessions) / len(sessions),
            "average_focus_score": sum(float(s.focus_score) for s in sessions) / len(sessions),
            "average_productivity_score": sum(float(s.productivity_score) for s in sessions) / len(sessions),
            "total_pages_visited": sum(s.pages_visited for s in sessions),
            "total_pomodoro_cycles": sum(s.pomodoro_cycles for s in sessions)
        }
    
    def _calculate_trends(self, sessions: List[StudySession], granularity: str) -> List[Dict[str, Any]]:
        """Calculate trends over time"""
        if not sessions:
            return []
        
        # Group sessions by time period
        trends = {}
        
        for session in sessions:
            if granularity == "daily":
                key = session.start_time.date()
            elif granularity == "weekly":
                key = session.start_time.isocalendar()[:2]  # Year, week
            elif granularity == "monthly":
                key = (session.start_time.year, session.start_time.month)
            else:  # hourly
                key = session.start_time.replace(minute=0, second=0, microsecond=0)
            
            if key not in trends:
                trends[key] = {
                    "period": str(key),
                    "sessions": [],
                    "total_minutes": 0,
                    "active_minutes": 0,
                    "pages_visited": 0,
                    "focus_scores": [],
                    "productivity_scores": []
                }
            
            trends[key]["sessions"].append(session)
            trends[key]["total_minutes"] += session.total_minutes
            trends[key]["active_minutes"] += session.active_minutes
            trends[key]["pages_visited"] += session.pages_visited
            trends[key]["focus_scores"].append(float(session.focus_score))
            trends[key]["productivity_scores"].append(float(session.productivity_score))
        
        # Calculate averages
        result = []
        for key, data in sorted(trends.items()):
            avg_focus = sum(data["focus_scores"]) / len(data["focus_scores"]) if data["focus_scores"] else 0
            avg_productivity = sum(data["productivity_scores"]) / len(data["productivity_scores"]) if data["productivity_scores"] else 0
            
            result.append({
                "period": data["period"],
                "session_count": len(data["sessions"]),
                "total_minutes": data["total_minutes"],
                "active_minutes": data["active_minutes"],
                "pages_visited": data["pages_visited"],
                "average_focus_score": round(avg_focus, 2),
                "average_productivity_score": round(avg_productivity, 2),
                "efficiency": round(data["active_minutes"] / data["total_minutes"], 2) if data["total_minutes"] > 0 else 0
            })
        
        return result
    
    def _calculate_performance_metrics(self, sessions: List[StudySession]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not sessions:
            return {}
        
        # Calculate percentiles
        focus_scores = [float(s.focus_score) for s in sessions]
        productivity_scores = [float(s.productivity_score) for s in sessions]
        session_lengths = [s.total_minutes for s in sessions]
        
        focus_scores.sort()
        productivity_scores.sort()
        session_lengths.sort()
        
        def percentile(data, p):
            k = (len(data) - 1) * p
            f = int(k)
            c = k - f
            if f == len(data) - 1:
                return data[f]
            return data[f] * (1 - c) + data[f + 1] * c
        
        return {
            "focus_score_percentiles": {
                "25th": round(percentile(focus_scores, 0.25), 2),
                "50th": round(percentile(focus_scores, 0.5), 2),
                "75th": round(percentile(focus_scores, 0.75), 2),
                "90th": round(percentile(focus_scores, 0.9), 2)
            },
            "productivity_score_percentiles": {
                "25th": round(percentile(productivity_scores, 0.25), 2),
                "50th": round(percentile(productivity_scores, 0.5), 2),
                "75th": round(percentile(productivity_scores, 0.75), 2),
                "90th": round(percentile(productivity_scores, 0.9), 2)
            },
            "session_length_percentiles": {
                "25th": int(percentile(session_lengths, 0.25)),
                "50th": int(percentile(session_lengths, 0.5)),
                "75th": int(percentile(session_lengths, 0.75)),
                "90th": int(percentile(session_lengths, 0.9))
            },
            "consistency_score": self._calculate_consistency_score(sessions)
        }
    
    def _calculate_reading_speed_metrics(
        self, 
        db: Session, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate reading speed metrics"""
        reading_speeds = db.query(ReadingSpeed).filter(
            ReadingSpeed.user_id == user_id,
            ReadingSpeed.created_at >= start_date,
            ReadingSpeed.created_at <= end_date
        ).all()
        
        if not reading_speeds:
            return {"average_wpm": 0, "average_ppm": 0, "trend": "no_data"}
        
        avg_wpm = sum(float(rs.words_per_minute) for rs in reading_speeds) / len(reading_speeds)
        avg_ppm = sum(float(rs.pages_per_minute) for rs in reading_speeds) / len(reading_speeds)
        
        # Calculate trend
        if len(reading_speeds) >= 2:
            first_half = reading_speeds[:len(reading_speeds)//2]
            second_half = reading_speeds[len(reading_speeds)//2:]
            
            first_avg = sum(float(rs.words_per_minute) for rs in first_half) / len(first_half)
            second_avg = sum(float(rs.words_per_minute) for rs in second_half) / len(second_half)
            
            if second_avg > first_avg * 1.05:
                trend = "improving"
            elif second_avg < first_avg * 0.95:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "average_wpm": round(avg_wpm, 2),
            "average_ppm": round(avg_ppm, 2),
            "trend": trend,
            "sample_size": len(reading_speeds)
        }
    
    def _calculate_focus_patterns(self, sessions: List[StudySession]) -> Dict[str, Any]:
        """Calculate focus patterns"""
        if not sessions:
            return {}
        
        # Analyze focus by time of day
        hourly_focus = {}
        for session in sessions:
            hour = session.start_time.hour
            if hour not in hourly_focus:
                hourly_focus[hour] = []
            hourly_focus[hour].append(float(session.focus_score))
        
        # Calculate averages
        avg_focus_by_hour = {}
        for hour, scores in hourly_focus.items():
            avg_focus_by_hour[hour] = sum(scores) / len(scores)
        
        # Find optimal hours
        optimal_hours = sorted(avg_focus_by_hour.keys(), 
                             key=lambda h: avg_focus_by_hour[h], reverse=True)[:3]
        
        # Analyze interruption patterns
        interruptions = [s.interruptions for s in sessions]
        avg_interruptions = sum(interruptions) / len(interruptions)
        
        return {
            "optimal_focus_hours": optimal_hours,
            "focus_by_hour": avg_focus_by_hour,
            "average_interruptions": round(avg_interruptions, 2),
            "best_focus_score": max(float(s.focus_score) for s in sessions),
            "focus_consistency": self._calculate_focus_consistency(sessions)
        }
    
    def _generate_recommendations(
        self, 
        sessions: List[StudySession], 
        performance: Dict[str, Any], 
        focus_patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        if not sessions:
            return ["Start your first study session to receive personalized recommendations!"]
        
        # Session length recommendations
        avg_length = sum(s.total_minutes for s in sessions) / len(sessions)
        if avg_length < 20:
            recommendations.append("Consider longer study sessions (25-45 minutes) for better focus")
        elif avg_length > 90:
            recommendations.append("Try shorter sessions with breaks to maintain focus")
        
        # Focus score recommendations
        avg_focus = sum(float(s.focus_score) for s in sessions) / len(sessions)
        if avg_focus < 0.6:
            recommendations.append("Minimize distractions and try the Pomodoro technique")
        elif avg_focus > 0.8:
            recommendations.append("Great focus! Consider tackling more challenging material")
        
        # Interruption recommendations
        avg_interruptions = sum(s.interruptions for s in sessions) / len(sessions)
        if avg_interruptions > 3:
            recommendations.append("Too many interruptions - try studying in a quieter environment")
        
        # Pomodoro recommendations
        pomodoro_users = sum(1 for s in sessions if s.pomodoro_cycles > 0)
        if pomodoro_users / len(sessions) < 0.3:
            recommendations.append("Try the Pomodoro technique for better time management")
        
        # Consistency recommendations
        if len(set(s.start_time.date() for s in sessions)) < len(sessions) * 0.7:
            recommendations.append("Study more consistently - daily sessions improve retention")
        
        return recommendations
    
    def _calculate_consistency_score(self, sessions: List[StudySession]) -> float:
        """Calculate consistency score"""
        if len(sessions) < 2:
            return 0.0
        
        # Calculate coefficient of variation for session lengths
        session_lengths = [s.total_minutes for s in sessions]
        mean_length = sum(session_lengths) / len(session_lengths)
        
        if mean_length == 0:
            return 0.0
        
        variance = sum((x - mean_length) ** 2 for x in session_lengths) / len(session_lengths)
        std_dev = variance ** 0.5
        cv = std_dev / mean_length
        
        # Convert to consistency score (lower CV = higher consistency)
        return max(0.0, 1.0 - cv)
    
    def _calculate_focus_consistency(self, sessions: List[StudySession]) -> float:
        """Calculate focus consistency score"""
        if len(sessions) < 2:
            return 0.0
        
        focus_scores = [float(s.focus_score) for s in sessions]
        mean_focus = sum(focus_scores) / len(focus_scores)
        
        if mean_focus == 0:
            return 0.0
        
        variance = sum((x - mean_focus) ** 2 for x in focus_scores) / len(focus_scores)
        std_dev = variance ** 0.5
        cv = std_dev / mean_focus
        
        return max(0.0, 1.0 - cv)
    
    def _analyze_hourly_performance(self, sessions: List[StudySession]) -> Dict[str, Any]:
        """Analyze performance by hour of day"""
        hourly_data = {}
        
        for session in sessions:
            hour = session.start_time.hour
            if hour not in hourly_data:
                hourly_data[hour] = {
                    "focus_scores": [],
                    "productivity_scores": [],
                    "session_lengths": []
                }
            
            hourly_data[hour]["focus_scores"].append(float(session.focus_score))
            hourly_data[hour]["productivity_scores"].append(float(session.productivity_score))
            hourly_data[hour]["session_lengths"].append(session.total_minutes)
        
        # Calculate averages and find best hours
        hour_performance = {}
        for hour, data in hourly_data.items():
            avg_focus = sum(data["focus_scores"]) / len(data["focus_scores"])
            avg_productivity = sum(data["productivity_scores"]) / len(data["productivity_scores"])
            combined_score = (avg_focus + avg_productivity) / 2
            
            hour_performance[hour] = combined_score
        
        best_hours = sorted(hour_performance.keys(), 
                           key=lambda h: hour_performance[h], reverse=True)[:3]
        
        return {
            "best_hours": best_hours,
            "performance_by_hour": hour_performance
        }
    
    def _analyze_daily_performance(self, sessions: List[StudySession]) -> Dict[str, Any]:
        """Analyze performance by day of week"""
        daily_data = {}
        
        for session in sessions:
            day = session.start_time.weekday()  # Monday = 0
            if day not in daily_data:
                daily_data[day] = {
                    "focus_scores": [],
                    "productivity_scores": [],
                    "session_count": 0
                }
            
            daily_data[day]["focus_scores"].append(float(session.focus_score))
            daily_data[day]["productivity_scores"].append(float(session.productivity_score))
            daily_data[day]["session_count"] += 1
        
        # Calculate averages and find best days
        day_performance = {}
        for day, data in daily_data.items():
            avg_focus = sum(data["focus_scores"]) / len(data["focus_scores"])
            avg_productivity = sum(data["productivity_scores"]) / len(data["productivity_scores"])
            combined_score = (avg_focus + avg_productivity) / 2
            
            day_performance[day] = combined_score
        
        best_days = sorted(day_performance.keys(), 
                          key=lambda d: day_performance[d], reverse=True)[:3]
        
        return {
            "best_days": best_days,
            "performance_by_day": day_performance
        }
    
    def _analyze_reading_speed_trends(self, reading_speeds: List[ReadingSpeed]) -> List[Dict[str, Any]]:
        """Analyze reading speed trends over time"""
        if not reading_speeds:
            return []
        
        # Sort by date
        reading_speeds.sort(key=lambda rs: rs.created_at)
        
        trends = []
        for i, rs in enumerate(reading_speeds):
            trends.append({
                "date": rs.created_at.isoformat(),
                "wpm": float(rs.words_per_minute),
                "ppm": float(rs.pages_per_minute),
                "content_type": rs.content_type,
                "difficulty": rs.difficulty_level
            })
        
        return trends
    
    def _analyze_focus_trends(self, sessions: List[StudySession]) -> List[Dict[str, Any]]:
        """Analyze focus score trends over time"""
        sessions.sort(key=lambda s: s.start_time)
        
        trends = []
        for session in sessions:
            trends.append({
                "date": session.start_time.isoformat(),
                "focus_score": float(session.focus_score),
                "session_length": session.total_minutes,
                "interruptions": session.interruptions
            })
        
        return trends
    
    def _analyze_productivity_trends(self, sessions: List[StudySession]) -> List[Dict[str, Any]]:
        """Analyze productivity trends over time"""
        sessions.sort(key=lambda s: s.start_time)
        
        trends = []
        for session in sessions:
            trends.append({
                "date": session.start_time.isoformat(),
                "productivity_score": float(session.productivity_score),
                "pages_visited": session.pages_visited,
                "active_minutes": session.active_minutes
            })
        
        return trends
    
    def _analyze_content_preferences(self, reading_speeds: List[ReadingSpeed]) -> Dict[str, Any]:
        """Analyze content type preferences"""
        content_performance = {}
        
        for rs in reading_speeds:
            content_type = rs.content_type
            if content_type not in content_performance:
                content_performance[content_type] = {
                    "speeds": [],
                    "count": 0
                }
            
            content_performance[content_type]["speeds"].append(float(rs.words_per_minute))
            content_performance[content_type]["count"] += 1
        
        # Calculate averages
        for content_type, data in content_performance.items():
            data["avg_speed"] = sum(data["speeds"]) / len(data["speeds"])
        
        return content_performance
    
    def _analyze_difficulty_performance(self, sessions: List[StudySession]) -> Dict[str, Any]:
        """Analyze performance by difficulty level"""
        # This would need PDF difficulty data - simplified for now
        return {
            "easy": {"avg_focus": 0.8, "avg_productivity": 0.75},
            "medium": {"avg_focus": 0.7, "avg_productivity": 0.65},
            "hard": {"avg_focus": 0.6, "avg_productivity": 0.55}
        }


# Create singleton instance
timer_service = TimerService()
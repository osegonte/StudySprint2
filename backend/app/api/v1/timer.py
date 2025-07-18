# backend/app/api/v1/timer.py
"""Timer & Analytics API Endpoints for Stage 3.4"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.config.database import get_db
from app.api.v1.auth import get_current_user
from app.services.timer_service import timer_service
from app.models import StudySession, PageTime, PomodoroSession, ReadingSpeed, TimeEstimate, UserStatistic
from app.schemas import (
    StudySessionCreate, StudySessionUpdate, StudySessionResponse, StudySessionWithStats,
    SessionActivityUpdate, SessionPauseRequest, SessionEndRequest,
    PageTimeCreate, PageTimeUpdate, PageTimeResponse, PageActivityEvent,
    PomodoroSessionCreate, PomodoroSessionUpdate, PomodoroSessionResponse, PomodoroSettings,
    ReadingSpeedCreate, ReadingSpeedResponse, TimeEstimateCreate, TimeEstimateResponse,
    UserStatisticResponse, StudyAnalyticsRequest, StudyAnalyticsResponse,
    ReadingPatternsResponse, TimeEstimationAccuracy, FocusAnalytics,
    SearchRequest, SearchResponse, TimerUpdateEvent, ProgressUpdateEvent
)
from app.utils.crud_router import create_user_owned_crud_router
from studysprint_db.models.user import User

# Create base CRUD router for sessions
session_router = create_user_owned_crud_router(
    model=StudySession,
    create_schema=StudySessionCreate,
    update_schema=StudySessionUpdate,
    response_schema=StudySessionResponse,
    name="sessions",
    service_class=type(timer_service)
)

# Create main router
router = APIRouter()
router.include_router(session_router, prefix="/sessions")

# ============================================================================
# STUDY SESSION MANAGEMENT
# ============================================================================

@router.post("/sessions/start", response_model=StudySessionResponse, status_code=status.HTTP_201_CREATED)
async def start_study_session(
    session_data: StudySessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new study session"""
    try:
        session = timer_service.start_session(
            db=db,
            session_data=session_data,
            user_id=str(current_user.id)
        )
        
        return StudySessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start session: {str(e)}"
        )

@router.put("/sessions/{session_id}/pause", response_model=StudySessionResponse)
async def pause_session(
    session_id: UUID,
    pause_request: SessionPauseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pause an active study session"""
    try:
        session = timer_service.pause_session(
            db=db,
            session_id=session_id,
            user_id=str(current_user.id),
            reason=pause_request.reason
        )
        
        return StudySessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to pause session: {str(e)}"
        )

@router.put("/sessions/{session_id}/resume", response_model=StudySessionResponse)
async def resume_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resume a paused study session"""
    try:
        session = timer_service.resume_session(
            db=db,
            session_id=session_id,
            user_id=str(current_user.id)
        )
        
        return StudySessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to resume session: {str(e)}"
        )

@router.post("/sessions/{session_id}/end", response_model=StudySessionResponse)
async def end_session(
    session_id: UUID,
    end_request: SessionEndRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End a study session"""
    try:
        session = timer_service.end_session(
            db=db,
            session_id=session_id,
            user_id=str(current_user.id),
            session_rating=end_request.session_rating,
            notes=end_request.notes
        )
        
        return StudySessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to end session: {str(e)}"
        )

@router.put("/sessions/{session_id}/activity", response_model=StudySessionResponse)
async def update_session_activity(
    session_id: UUID,
    activity: SessionActivityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update session activity metrics"""
    try:
        session = timer_service.update_session_activity(
            db=db,
            session_id=session_id,
            user_id=str(current_user.id),
            activity=activity
        )
        
        return StudySessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update activity: {str(e)}"
        )

@router.get("/sessions/active", response_model=Optional[StudySessionResponse])
async def get_active_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current active session"""
    try:
        session = timer_service.get_active_session(db, str(current_user.id))
        
        if session:
            return StudySessionResponse.from_orm(session)
        return None
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active session: {str(e)}"
        )

@router.get("/sessions/history", response_model=List[StudySessionResponse])
async def get_session_history(
    limit: int = Query(50, ge=1, le=200, description="Number of sessions to return"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's session history"""
    try:
        sessions = timer_service.get_session_history(
            db=db,
            user_id=str(current_user.id),
            limit=limit,
            days=days
        )
        
        return [StudySessionResponse.from_orm(s) for s in sessions]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session history: {str(e)}"
        )

@router.get("/sessions/{session_id}/details", response_model=StudySessionWithStats)
async def get_session_details(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed session information with statistics"""
    try:
        session = timer_service.get(db, id=session_id, user_id=str(current_user.id))
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get page times
        page_times = db.query(PageTime).filter(
            PageTime.session_id == session_id
        ).all()
        
        # Get pomodoro cycles
        pomodoro_cycles = db.query(PomodoroSession).filter(
            PomodoroSession.study_session_id == session_id
        ).all()
        
        # Calculate additional statistics
        statistics = {
            "efficiency_score": session.efficiency_score,
            "pages_per_minute": session.pages_visited / session.active_minutes if session.active_minutes > 0 else 0,
            "interruption_rate": session.interruptions / session.total_minutes if session.total_minutes > 0 else 0,
            "pause_frequency": session.pause_count / session.total_minutes if session.total_minutes > 0 else 0
        }
        
        session_response = StudySessionResponse.from_orm(session)
        return StudySessionWithStats(
            **session_response.dict(),
            statistics=statistics,
            page_times=[{
                "page_number": pt.page_number,
                "duration_seconds": pt.duration_seconds,
                "reading_speed_wpm": float(pt.reading_speed_wpm) if pt.reading_speed_wpm else 0,
                "engagement_score": pt.engagement_score
            } for pt in page_times],
            pomodoro_cycles=[{
                "cycle_number": pc.cycle_number,
                "cycle_type": pc.cycle_type,
                "completed": pc.completed,
                "focus_score": float(pc.focus_score)
            } for pc in pomodoro_cycles]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session details: {str(e)}"
        )

# ============================================================================
# PAGE-LEVEL TIMING
# ============================================================================

@router.post("/page-times/start", response_model=PageTimeResponse, status_code=status.HTTP_201_CREATED)
async def start_page_timer(
    page_data: PageTimeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start timing for a specific page"""
    try:
        page_time = timer_service.start_page_timer(
            db=db,
            page_data=page_data,
            user_id=str(current_user.id)
        )
        
        return PageTimeResponse.from_orm(page_time)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start page timer: {str(e)}"
        )

@router.post("/page-times/{page_time_id}/end", response_model=PageTimeResponse)
async def end_page_timer(
    page_time_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End timing for a specific page"""
    try:
        page_time = timer_service.end_page_timer(
            db=db,
            page_time_id=page_time_id,
            user_id=str(current_user.id)
        )
        
        return PageTimeResponse.from_orm(page_time)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to end page timer: {str(e)}"
        )

@router.put("/page-times/{page_time_id}/activity", response_model=PageTimeResponse)
async def update_page_activity(
    page_time_id: UUID,
    activity: PageTimeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update page activity metrics"""
    try:
        page_time = timer_service.update_page_activity(
            db=db,
            page_time_id=page_time_id,
            user_id=str(current_user.id),
            activity=activity
        )
        
        return PageTimeResponse.from_orm(page_time)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update page activity: {str(e)}"
        )

@router.post("/page-times/{page_time_id}/activity-event")
async def record_page_activity_event(
    page_time_id: UUID,
    event: PageActivityEvent,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record real-time page activity event"""
    try:
        # Get page time
        page_time = db.query(PageTime).filter(
            PageTime.id == page_time_id
        ).join(StudySession).filter(
            StudySession.user_id == current_user.id
        ).first()
        
        if not page_time:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page timer not found"
            )
        
        # Update based on event type
        if event.event_type == "click":
            page_time.click_count += 1
        elif event.event_type == "scroll":
            page_time.scroll_count += 1
            if event.position:
                if not page_time.scroll_positions:
                    page_time.scroll_positions = []
                page_time.scroll_positions.append({
                    "timestamp": event.timestamp.isoformat(),
                    "position": event.position
                })
        elif event.event_type == "zoom":
            page_time.zoom_changes += 1
            if event.data:
                if not page_time.zoom_levels:
                    page_time.zoom_levels = []
                page_time.zoom_levels.append({
                    "timestamp": event.timestamp.isoformat(),
                    "zoom_level": event.data.get("zoom_level", 1.0)
                })
        elif event.event_type == "note":
            page_time.notes_created += 1
        elif event.event_type == "highlight":
            page_time.highlights_made += 1
        elif event.event_type == "bookmark":
            page_time.bookmarks_added += 1
        
        # Update total activity count
        page_time.activity_count = (
            page_time.click_count + 
            page_time.scroll_count + 
            page_time.zoom_changes
        )
        
        db.commit()
        
        return {"message": "Activity event recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to record activity event: {str(e)}"
        )

# ============================================================================
# POMODORO TIMER
# ============================================================================

@router.post("/pomodoro/start", response_model=PomodoroSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_pomodoro_cycle(
    pomodoro_data: PomodoroSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new Pomodoro cycle"""
    try:
        pomodoro = timer_service.start_pomodoro_cycle(
            db=db,
            pomodoro_data=pomodoro_data,
            user_id=str(current_user.id)
        )
        
        return PomodoroSessionResponse.from_orm(pomodoro)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start Pomodoro cycle: {str(e)}"
        )

@router.post("/pomodoro/{pomodoro_id}/complete", response_model=PomodoroSessionResponse)
async def complete_pomodoro_cycle(
    pomodoro_id: UUID,
    completion_data: PomodoroSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete a Pomodoro cycle"""
    try:
        pomodoro = timer_service.complete_pomodoro_cycle(
            db=db,
            pomodoro_id=pomodoro_id,
            user_id=str(current_user.id),
            effectiveness_rating=completion_data.effectiveness_rating,
            interruptions=completion_data.interruptions or 0
        )
        
        return PomodoroSessionResponse.from_orm(pomodoro)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to complete Pomodoro cycle: {str(e)}"
        )

@router.get("/pomodoro/settings", response_model=PomodoroSettings)
async def get_pomodoro_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's Pomodoro settings"""
    try:
        # Get from user preferences
        from studysprint_db.models.user import UserPreferences
        
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        
        if not preferences:
            # Return default settings
            return PomodoroSettings()
        
        return PomodoroSettings(
            work_duration=preferences.default_session_duration,
            short_break_duration=preferences.break_duration,
            long_break_duration=preferences.long_break_duration,
            auto_start_breaks=preferences.auto_start_breaks,
            sound_enabled=preferences.sound_enabled
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Pomodoro settings: {str(e)}"
        )

@router.put("/pomodoro/settings", response_model=PomodoroSettings)
async def update_pomodoro_settings(
    settings: PomodoroSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's Pomodoro settings"""
    try:
        from studysprint_db.models.user import UserPreferences
        
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        
        if not preferences:
            preferences = UserPreferences(user_id=current_user.id)
            db.add(preferences)
        
        # Update settings
        preferences.default_session_duration = settings.work_duration
        preferences.break_duration = settings.short_break_duration
        preferences.long_break_duration = settings.long_break_duration
        preferences.auto_start_breaks = settings.auto_start_breaks
        preferences.sound_enabled = settings.sound_enabled
        
        db.commit()
        
        return settings
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Pomodoro settings: {str(e)}"
        )

# ============================================================================
# SMART TIME ESTIMATION
# ============================================================================

@router.post("/estimates", response_model=TimeEstimateResponse, status_code=status.HTTP_201_CREATED)
async def create_time_estimate(
    estimate_data: TimeEstimateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a smart time estimate"""
    try:
        estimate = timer_service.create_time_estimate(
            db=db,
            estimate_data=estimate_data,
            user_id=str(current_user.id)
        )
        
        return TimeEstimateResponse.from_orm(estimate)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create time estimate: {str(e)}"
        )

@router.get("/estimates", response_model=List[TimeEstimateResponse])
async def get_time_estimates(
    pdf_id: Optional[UUID] = Query(None, description="Filter by PDF ID"),
    topic_id: Optional[UUID] = Query(None, description="Filter by topic ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get smart time estimates"""
    try:
        estimates = timer_service.get_smart_estimates(
            db=db,
            user_id=str(current_user.id),
            pdf_id=pdf_id,
            topic_id=topic_id
        )
        
        return [TimeEstimateResponse.from_orm(e) for e in estimates]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get time estimates: {str(e)}"
        )

@router.get("/estimates/pdf/{pdf_id}/completion")
async def get_pdf_completion_estimate(
    pdf_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get smart completion estimate for a PDF"""
    try:
        estimate = timer_service.calculate_reading_completion_estimate(
            db=db,
            pdf_id=pdf_id,
            user_id=str(current_user.id)
        )
        
        return estimate
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate completion estimate: {str(e)}"
        )

# ============================================================================
# ANALYTICS & INSIGHTS
# ============================================================================

@router.post("/analytics/study", response_model=StudyAnalyticsResponse)
async def get_study_analytics(
    request: StudyAnalyticsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive study analytics"""
    try:
        analytics = timer_service.get_study_analytics(
            db=db,
            user_id=str(current_user.id),
            request=request
        )
        
        return StudyAnalyticsResponse(**analytics)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get study analytics: {str(e)}"
        )

@router.get("/analytics/reading-patterns", response_model=ReadingPatternsResponse)
async def get_reading_patterns(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reading patterns and optimal study times"""
    try:
        patterns = timer_service.get_reading_patterns(
            db=db,
            user_id=str(current_user.id),
            days=days
        )
        
        return ReadingPatternsResponse(**patterns)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reading patterns: {str(e)}"
        )

@router.get("/analytics/focus")
async def get_focus_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get focus and attention analytics"""
    try:
        # Get recent sessions
        sessions = timer_service.get_session_history(
            db=db,
            user_id=str(current_user.id),
            limit=1000,
            days=days
        )
        
        if not sessions:
            return FocusAnalytics(
                average_focus_score=0.0,
                focus_trends=[],
                distraction_patterns={},
                optimal_session_length=25,
                interruption_analysis={},
                improvement_recommendations=["Start your first study session to get focus analytics!"]
            )
        
        # Calculate focus metrics
        focus_scores = [float(s.focus_score) for s in sessions]
        avg_focus = sum(focus_scores) / len(focus_scores)
        
        # Calculate trends
        focus_trends = []
        for session in sessions[-30:]:  # Last 30 sessions
            focus_trends.append({
                "date": session.start_time.isoformat(),
                "focus_score": float(session.focus_score),
                "interruptions": session.interruptions,
                "session_length": session.total_minutes
            })
        
        # Analyze distractions
        interruptions = [s.interruptions for s in sessions]
        avg_interruptions = sum(interruptions) / len(interruptions)
        
        distraction_patterns = {
            "average_interruptions_per_session": round(avg_interruptions, 2),
            "sessions_with_high_interruptions": len([s for s in sessions if s.interruptions > 5]),
            "most_distracting_time": "afternoon"  # Simplified
        }
        
        # Find optimal session length
        session_lengths = [s.total_minutes for s in sessions]
        optimal_length = sum(session_lengths) / len(session_lengths)
        
        # Interruption analysis
        interruption_analysis = {
            "total_interruptions": sum(interruptions),
            "interruption_rate": round(avg_interruptions / optimal_length, 3) if optimal_length > 0 else 0,
            "worst_session": max(interruptions) if interruptions else 0,
            "improvement_trend": "stable"  # Simplified
        }
        
        # Generate recommendations
        recommendations = []
        if avg_focus < 0.6:
            recommendations.append("Try studying in a quieter environment")
            recommendations.append("Use the Pomodoro technique for better focus")
        if avg_interruptions > 3:
            recommendations.append("Turn off notifications during study sessions")
        if optimal_length > 90:
            recommendations.append("Consider shorter sessions with breaks")
        
        return FocusAnalytics(
            average_focus_score=round(avg_focus, 2),
            focus_trends=focus_trends,
            distraction_patterns=distraction_patterns,
            optimal_session_length=int(optimal_length),
            interruption_analysis=interruption_analysis,
            improvement_recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get focus analytics: {str(e)}"
        )

@router.get("/analytics/time-estimation-accuracy")
async def get_time_estimation_accuracy(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get time estimation accuracy analysis"""
    try:
        estimates = db.query(TimeEstimate).filter(
            TimeEstimate.user_id == current_user.id,
            TimeEstimate.accuracy_score.isnot(None)
        ).all()
        
        if not estimates:
            return TimeEstimationAccuracy(
                overall_accuracy=0.0,
                accuracy_by_type={},
                variance_trends=[],
                improvement_suggestions=["Complete more sessions to get estimation accuracy data!"]
            )
        
        # Calculate overall accuracy
        accuracies = [float(e.accuracy_score) for e in estimates]
        overall_accuracy = sum(accuracies) / len(accuracies)
        
        # Calculate accuracy by type
        accuracy_by_type = {}
        for estimate in estimates:
            est_type = estimate.estimate_type
            if est_type not in accuracy_by_type:
                accuracy_by_type[est_type] = []
            accuracy_by_type[est_type].append(float(estimate.accuracy_score))
        
        # Calculate averages
        for est_type, scores in accuracy_by_type.items():
            accuracy_by_type[est_type] = round(sum(scores) / len(scores), 2)
        
        # Calculate variance trends
        variance_trends = []
        for estimate in estimates[-20:]:  # Last 20 estimates
            variance_trends.append({
                "date": estimate.created_at.isoformat(),
                "accuracy": float(estimate.accuracy_score),
                "variance_percentage": float(estimate.variance_percentage) if estimate.variance_percentage else 0,
                "estimate_type": estimate.estimate_type
            })
        
        # Generate improvement suggestions
        suggestions = []
        if overall_accuracy < 0.7:
            suggestions.append("Your time estimates are often inaccurate - try tracking time more carefully")
        if accuracy_by_type.get("completion", 0) < 0.6:
            suggestions.append("Completion estimates need work - factor in your reading speed")
        if len(estimates) < 10:
            suggestions.append("Complete more sessions to improve estimation accuracy")
        
        return TimeEstimationAccuracy(
            overall_accuracy=round(overall_accuracy, 2),
            accuracy_by_type=accuracy_by_type,
            variance_trends=variance_trends,
            improvement_suggestions=suggestions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get time estimation accuracy: {str(e)}"
        )

# ============================================================================
# READING SPEED TRACKING
# ============================================================================

@router.post("/reading-speed", response_model=ReadingSpeedResponse, status_code=status.HTTP_201_CREATED)
async def record_reading_speed(
    speed_data: ReadingSpeedCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record reading speed data"""
    try:
        from datetime import datetime, timezone
        
        reading_speed = ReadingSpeed(
            user_id=current_user.id,
            pdf_id=speed_data.pdf_id,
            topic_id=speed_data.topic_id,
            session_id=speed_data.session_id,
            pages_per_minute=speed_data.pages_per_minute,
            words_per_minute=speed_data.words_per_minute,
            characters_per_minute=speed_data.words_per_minute * 5,  # Estimate
            content_type=speed_data.content_type,
            difficulty_level=speed_data.difficulty_level,
            estimated_words=speed_data.estimated_words,
            time_of_day=datetime.now(timezone.utc).hour,
            day_of_week=datetime.now(timezone.utc).weekday(),
            session_duration=speed_data.session_duration,
            environmental_factors=speed_data.environmental_factors
        )
        
        db.add(reading_speed)
        db.commit()
        db.refresh(reading_speed)
        
        return ReadingSpeedResponse.from_orm(reading_speed)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to record reading speed: {str(e)}"
        )

@router.get("/reading-speed", response_model=List[ReadingSpeedResponse])
async def get_reading_speeds(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reading speed history"""
    try:
        from datetime import datetime, timezone, timedelta
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        reading_speeds = db.query(ReadingSpeed).filter(
            ReadingSpeed.user_id == current_user.id,
            ReadingSpeed.created_at >= start_date
        ).order_by(ReadingSpeed.created_at.desc()).all()
        
        return [ReadingSpeedResponse.from_orm(rs) for rs in reading_speeds]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reading speeds: {str(e)}"
        )

# ============================================================================
# STATISTICS & REPORTS
# ============================================================================

@router.get("/statistics/{stat_type}", response_model=List[UserStatisticResponse])
async def get_user_statistics(
    stat_type: str = Query(..., regex="^(daily|weekly|monthly|lifetime)$"),
    limit: int = Query(30, ge=1, le=365, description="Number of statistics to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics by type"""
    try:
        statistics = db.query(UserStatistic).filter(
            UserStatistic.user_id == current_user.id,
            UserStatistic.stat_type == stat_type
        ).order_by(UserStatistic.stat_date.desc()).limit(limit).all()
        
        return [UserStatisticResponse.from_orm(stat) for stat in statistics]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user statistics: {str(e)}"
        )

# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def timer_health_check():
    """Health check for timer service"""
    return {
        "status": "healthy",
        "service": "timer_analytics",
        "version": "2.0.0",
        "features": [
            "study_session_management",
            "page_level_timing",
            "pomodoro_integration",
            "smart_time_estimation",
            "reading_speed_tracking",
            "comprehensive_analytics",
            "focus_analysis",
            "performance_insights",
            "real_time_activity_tracking"
        ]
    }
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from backend.db.models import User, ChatSession, Message, ChannelType, SessionLocal
from backend.core.ai_engine import get_ai_engine
import datetime

class MessageDispatcher:
    def __init__(self):
        self.ai_engine = get_ai_engine()

    async def process_message(
        self, 
        external_user_id: str, 
        content: str, 
        channel: ChannelType,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Normalizes any incoming message, logs everything, 
        gets AI response, and returns the response details.
        """
        db = SessionLocal()
        try:
            # 1. Ensure User exists
            user = db.query(User).filter(User.external_id == external_user_id).first()
            if not user:
                user = User(external_id=external_user_id, username=username)
                db.add(user)
                db.flush()

            # 2. Find or create ChatSession for this channel
            session = db.query(ChatSession).filter(
                ChatSession.user_id == user.id,
                ChatSession.channel == channel
            ).first()
            
            if not session:
                session = ChatSession(user_id=user.id, channel=channel)
                db.add(session)
                db.flush()

            # 3. Log User Message
            user_msg = Message(session_id=session.id, sender_type="user", content=content)
            db.add(user_msg)
            db.flush()

            # 4. Generate AI Response
            # In a real app, we'd pull history from the DB here
            history = self._get_session_history(db, session.id)
            ai_response_text = await self.ai_engine.generate_response(content, history)

            # 5. Log AI Message
            ai_msg = Message(session_id=session.id, sender_type="ai", content=ai_response_text)
            db.add(ai_msg)
            db.commit()

            return {
                "user_id": external_user_id,
                "channel": channel.value,
                "user_message": content,
                "ai_response": ai_response_text,
                "timestamp": ai_msg.timestamp.isoformat()
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def _get_session_history(self, db: Session, session_id: int, limit: int = 10):
        messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp.desc()).limit(limit).all()
        return [{"role": m.sender_type, "content": m.content} for m in reversed(messages)]

# Singleton instance for easy access
dispatcher = MessageDispatcher()

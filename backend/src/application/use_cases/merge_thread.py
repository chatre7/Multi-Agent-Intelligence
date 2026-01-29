from datetime import datetime
import uuid

from src.application.use_cases.knowledge import UploadKnowledgeUseCase
from src.domain.entities.conversation import Conversation, ThreadStatus
from src.domain.repositories.conversation_repository import IConversationRepository


class MergeThreadUseCase:
    """Use case for merging a thread into the Knowledge Base."""

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        upload_knowledge_use_case: UploadKnowledgeUseCase,
    ):
        self._conversation_repo = conversation_repo
        self._upload_knowledge_use_case = upload_knowledge_use_case

    def execute(self, conversation_id: str) -> None:
        conversation = self._conversation_repo.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if conversation.status == ThreadStatus.MERGED:
            return  # Already merged

        # 1. Fetch content (Simple concatenation for MVP)
        messages = self._conversation_repo.list_messages(conversation_id, limit=500)
        
        # Simple Markdown Formatting
        content_lines = [f"# Thread: {conversation.title or 'Untitled Thread'}", ""]
        content_lines.append(f"**Merged Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content_lines.append(f"**Participants:** {', '.join(conversation.reviewers)}")
        content_lines.append("")
        content_lines.append("## Transcript")
        content_lines.append("")
        
        for msg in messages:
            role_icon = "👤" if msg.role == "user" else "🤖"
            content_lines.append(f"### {role_icon} {msg.role.upper()}")
            content_lines.append(msg.content)
            content_lines.append("")

        full_content = "\n".join(content_lines)
        filename = f"thread_{conversation_id}_{datetime.now().strftime('%Y%m%d')}.md"

        # 2. Upload to Knowledge Base
        self._upload_knowledge_use_case.execute(
            filename=filename,
            content=full_content,
            content_type="text/markdown"
        )

        # 3. Update Status
        conversation.status = ThreadStatus.MERGED
        conversation.touch()
        self._conversation_repo.update_conversation(conversation)

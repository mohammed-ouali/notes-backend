from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment


class AttachmentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, attachment_id: int) -> Attachment | None:
        result = await self.session.execute(
            select(Attachment).where(Attachment.id == attachment_id)
        )

        return result.scalar_one_or_none()

    async def get_by_note_id(self, note_id: int) -> list[Attachment]:
        result = await self.session.execute(
            select(Attachment)
            .where(Attachment.note_id == note_id)
            .order_by(Attachment.created_at)
        )

        return list(result.scalars().all())

    async def get_total_size_by_note_id(self, note_id: int) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.sum(Attachment.size_bytes), 0))
            .where(Attachment.note_id == note_id)
        )

        return result.scalar_one()

    async def create(self, attachment: Attachment) -> Attachment:
        self.session.add(attachment)
        await self.session.commit()
        await self.session.refresh(attachment)

        return attachment

    async def delete(self, attachment: Attachment) -> None:
        await self.session.delete(attachment)
        await self.session.commit()
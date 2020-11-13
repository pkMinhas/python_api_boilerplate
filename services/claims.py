from database_manager import DatabaseManager as DM
from constants import ClaimsManagement
from datetime import datetime


class ClaimsManagementService:
    @classmethod
    def update_claims(cls, user_id, is_admin, is_super_admin, updated_by_user_id=None):
        assert updated_by_user_id is not None
        DM.db[ClaimsManagement.COLLECTION_NAME].update_one(
            filter={ClaimsManagement.USER_ID: user_id},
            update={"$set": {
                ClaimsManagement.IS_ADMIN: is_admin,
                ClaimsManagement.IS_SUPER_ADMIN: is_super_admin,
                ClaimsManagement.LAST_MODIFIED_BY: updated_by_user_id,
                ClaimsManagement.LAST_MODIFIED_AT: datetime.utcnow()
            }},
            upsert=True
        )

    @classmethod
    def get_user_claims(cls, user_id):
        doc = DM.db[ClaimsManagement.COLLECTION_NAME].find_one({ClaimsManagement.USER_ID: user_id})
        is_admin = False
        is_super_admin = False
        last_modified_by = None
        last_modified_at = None
        if doc is not None:
            is_admin = doc.get(ClaimsManagement.IS_ADMIN, False)
            is_super_admin = doc.get(ClaimsManagement.IS_SUPER_ADMIN, False)
            last_modified_by = doc.get(ClaimsManagement.LAST_MODIFIED_BY)
            last_modified_at = doc.get(ClaimsManagement.LAST_MODIFIED_AT)

        return {
            "isAdmin": is_admin,
            "isSuperAdmin": is_super_admin,
            "lastModifiedBy": last_modified_by,
            "lastModifiedAt": last_modified_at
        }

    @classmethod
    def get_all_entries(cls):
        cursor = DM.db[ClaimsManagement.COLLECTION_NAME].find()
        result = []
        for doc in cursor:
            user_id = doc.get(ClaimsManagement.USER_ID)
            is_admin = doc.get(ClaimsManagement.IS_ADMIN, False)
            is_super_admin = doc.get(ClaimsManagement.IS_SUPER_ADMIN, False)
            last_modified_by = doc.get(ClaimsManagement.LAST_MODIFIED_BY)
            last_modified_at = doc.get(ClaimsManagement.LAST_MODIFIED_AT)

            result.append({
                "userId": user_id,
                "isAdmin": is_admin,
                "isSuperAdmin": is_super_admin,
                "lastModifiedBy": last_modified_by,
                "lastModifiedAt": last_modified_at
            })
        return result


from flask_restful import Resource, request
from application_error import ApplicationError
from services.security import super_admin_required, admin_required
from services.claims import ClaimsManagementService
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required
)
from schemas.claims import UserClaimsUpdateSchema


class ClaimsList(Resource):
    # Only super admin can get a list of claims saved for the users
    @super_admin_required
    def get(self):
        """Gets list of all claims registered in the application"""
        return ClaimsManagementService.get_all_entries()


class UpdateClaims(Resource):
    # Only super admin can update the claims list
    @super_admin_required
    def put(self):
        current_user_id = get_jwt_identity()
        data = UserClaimsUpdateSchema().load(request.json)
        user_id = data["userId"]
        is_admin = data["isAdmin"]
        is_super_admin = data["isSuperAdmin"]
        ClaimsManagementService.update_claims(user_id=user_id,
                                              is_admin=is_admin,
                                              is_super_admin=is_super_admin,
                                              updated_by_user_id=current_user_id)
        return {}, 200


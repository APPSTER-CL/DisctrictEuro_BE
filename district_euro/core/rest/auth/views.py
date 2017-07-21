from rest_framework_jwt.views import ObtainJSONWebToken


class DistrictObtainJSONWebToken(ObtainJSONWebToken):
    def post(self, *args, **kwargs):
        '''
        Authenticates a user.
        ---
        parameters:
            - name: email
              required: True
              type: string
              paramType: form
            - name: password
              required: True
              type: string
              paramType: form

        type:
            token:
                required: True
                type: string
            token_expiration:
                required: True
                type: date
            user:
                required: True
                type: user information

        omit_parameters:
            - body
        '''
        return super(DistrictObtainJSONWebToken, self).post(*args, **kwargs)


obtain_jwt_token = DistrictObtainJSONWebToken.as_view()

from django.contrib.auth import authenticate
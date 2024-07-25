import ldap
from ldap.ldapobject import SimpleLDAPObject
from fastapi import HTTPException, APIRouter

router = APIRouter()
endpoint_name = "ldap_info"
class LDAPClient:
    def __init__(self, server_uri: str, bind_dn: str, bind_password: str):
        self.server_uri = server_uri
        self.bind_dn = bind_dn
        self.bind_password = bind_password
        self.conn: SimpleLDAPObject = None

    def connect(self):
        self.conn = ldap.initialize(self.server_uri)
        self.conn.simple_bind_s(self.bind_dn, self.bind_password)

    def search_user(self, username: str):
        search_filter = f"(uid={username})"
        base_dn = "ou=develop,dc=ldap,dc=example,dc=com"  # Adjust this to your LDAP's base DN
        try:
            self.connect()
            result = self.conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter)
            # Assuming the user entry is the first entry in the search result
            user_entry = result[0] if result else None
            if user_entry:
                # Extract the DN and attributes from the result
                user_dn, user_attributes = user_entry
                return {"dn": user_dn, "attributes": user_attributes}
            else:
                return None
        except ldap.LDAPError as e:
            print(f"LDAP error: {e}")
            return None
        finally:
            self.disconnect()

    def disconnect(self):
        if self.conn:
            self.conn.unbind_s()



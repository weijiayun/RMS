import psycopg2

class Role(object):
    def __init__(self, roleId, roleName, isLogin):
        self.id = roleId
        self.name = roleName
        self.parents = {}
        self.parentTree = {}
        self.resources = {}
        self.is_Login = isLogin

    def __str__(self):
        return r'<Role:(id:{0}, name: {1})>'.format(self.id, self.name)
    __repr__ = __str__

    def getId(self):
        return self.id

    def getName(self):
        return self.name

    def getResources(self):
        return self.resources

    def isLogin(self):
        return self.is_Login

    def getParents(self):
        return self.parents

    def getParentTree(self):
        self.parentTree.clear()
        self.__getAllParents(self)
        return self.parentTree

    def __getAllParents(self, role):
        for pid, parent in role.getParents().items():
            if pid == role.getId():
                self.parentTree[pid] = parent
            else:
                self.__getAllParents(parent)

    def getAllResources(self):
        self.parentTree.clear()
        self.__getAllParents(self)
        dictmerged = {}
        for pId, parent in self.getParentTree().items():
            dictmerged.update(parent.getResources())
        return dictmerged

    def addParent(self, parentRoles):
        if isinstance(parentRoles, Role):
            if not self.isChildOf(parentRoles):
                self.parents[parentRoles.getId()] = parentRoles
                return True
            else:
                raise Exception('Error: Cyclic inheritance:(childRole:{0}, ParentRole:{1})'.format(self, parentRoles))
        else:
            raise TypeError

    def removeParent(self, parentRoles):
        if isinstance(parentRoles, Role):
            if parentRoles.getId() in self.getParents():
                del self.parents[parentRoles.getId()]
                return True
            else:
                return False
        else:
            raise TypeError

    def addResource(self, res, permissionIds):
        if isinstance(res, Resource):
            if not res.getId() in self.getResources():
                self.resources[res.getId()] = ResPermsPair(res, permissionIds)
                return True
        else:
            raise TypeError("please input the instance of type Resource")

    def isChildOf(self, pRole):
        if isinstance(pRole, Role):
            try:
                roleParents = pRole.getParentTree()
                if self.getId() in roleParents:
                    return True
                else:
                    return False
            except Exception("Error: Inquiry isChildof Child:{0} Parent:{1}".format(self, pRole)) as e:
                raise e
        else:
            raise TypeError("Error: <{0}>.isChildOf".format(self))

    def removeResource(self, resource):
        if isinstance(resource, Resource):
            if resource.getId() in self.getResources():
                del self.resources[resource.getId()]
                return True
        else:
            raise TypeError('remove resource need input the Resource instance in role: <{0}>'.format(self))

    def hasPermission(self, resourceId, permission):
        self.parentTree.clear()
        self.__getAllParents(self)
        result = False
        for pId, pRole in self.parentTree.items():
            if resourceId in pRole.getResources():
                result = result or permission in pRole.getResources()[resourceId].getPermissions().values()
            else:
                for resId, resPerms in pRole.getResources().items():
                    if resPerms.getResource().getIsGroup() == 1:
                        if resourceId in resPerms.getResource().getMembers():
                            result = result or permission in resPerms.getPermissions().values()
        return result

class Resource(object):
    def __init__(self, resId, name, resourceType, contentId, isGroup):
        self.id = resId
        self.name = name
        self.resourceType = resourceType
        self.contentId = contentId
        self.isGroup = isGroup

    def __str__(self):
        return "Resource <id:{0},name: {1}, isGroup:{2}>".format(self.id, self.name, self.isGroup)
    __repr__ = __str__

    def getId(self):
        return self.id

    def getName(self):
        return self.name

    def getResourceType(self):
        return self.resourceType

    def getContentId(self):
        return self.contentId

    def getIsGroup(self):
        return self.isGroup

class ResPermsPair(object):
    def __init__(self, resource, permissionIds):
        if isinstance(resource, Resource):
            self.resource = resource
            permissions = resource.getResourceType().getPermissions()
            self.permissions = {}
            if permissionIds:
                for permId in permissionIds:
                    if permId in permissions:
                        self.permissions[permId] = permissions[permId]
                    else:
                        raise Exception("ResourceType<{0}> has no permission:<id:{0}>"
                                        .format(resource.getResourceType().getName(), permId))
            else:
                self.permissions = permissions
        else:
            raise Exception("ResPermsPair need Resource instance")

    def getResource(self):
        return self.resource

    def getPermissions(self):
        return self.permissions

    def addPermission(self, permissionId):
        if permissionId in self.resource.getResourceType().getPermissions():
            self.permissions[permissionId] = self.resource.getResourceType().getPermissions()[permissionId]
            return True
        else:
            raise Exception("ResourceType<{0}> has no permission:<id:{0}>"
                                        .format(self.resource.getResourceType().getName(), permissionId))

    def removePermission(self, permissionId):
        if permissionId in self.permissions:
            del self.permissions[permissionId]
            return True
        else:
            raise Exception("Resource for current user has no permission<id:{0}>".format(permissionId))

class ResGroup(Resource):
    def __init__(self, resourceId, resourceName, resourceType, contentId=None, isGroup=1):
        super(ResGroup, self).__init__(resourceId, resourceName, resourceType, contentId, isGroup)
        self.groupMember = {}

    def addMember(self, resource):
        if isinstance(resource, Resource):
            if self.getResourceType() == resource.getResourceType():
                if resource.getId() not in self.getMembers():
                    self.groupMember[resource.getId()] = resource
            else:
                raise TypeError("group need a member that have a same resource type")
        else:
            raise TypeError("group member need a Resource instance")
    
    def removeMember(self, resource):
        if isinstance(resource, Resource):
            if resource.getId() in self.getMembers():
                del self.groupMember[resource.getId()]

    def getMembers(self):
        return self.groupMember

class ResourceType(object):

    def __init__(self, resourceTypeId, resourceTypeName, description=None):
        self.id = resourceTypeId
        self.name = resourceTypeName
        self.description = description
        self.permissions = {}

    def __repr__(self):
        return r'ResourceType<Id:{0}, name:{1}, permissions: {2}>'.format(self.id, self.name, self.permissions)
    __str__ = __repr__

    def addPermission(self, mapping):
        for permId, permName in mapping.items():
            if permId not in self.permissions:
                self.permissions[permId] = permName

    def removePermission(self, permId):
        if permId in self.permissions:
            del self.permissions[permId]
            return True
        else:
            return False

    def getPermissions(self):
        return self.permissions

    def getName(self):
        return self.name

    def getId(self):
        return self.id

    def getDesc(self):
        return self.description

class RoleManager(object):
    def __init__(self, db, redisdb):
        self.db = db
        self.redisdb = redisdb
        self.allRoles = {}
        self.allResources = {}
        self.allResourceTypes = {}
        self.permissionTable = self.getPermissionTable()
        roleTable = self.getRoleTable()
        self.resourceTable = self.getResourceTable()
        resourceTypeTable = self.getResourceTypeTable()

        for rtid, rtName, desc in resourceTypeTable:
            resourceTypetmp = ResourceType(rtid, rtName, desc)
            resourceTypetmp.addPermission(self.getResourceTypePermissions(rtid))
            self.allResourceTypes[rtid] = resourceTypetmp

        for resId, row in self.resourceTable.items():
            if row[4] == 0:
                tempResource = Resource(
                    resId=row[0],
                    name=row[1],
                    resourceType=self.allResourceTypes[row[2]],
                    contentId=row[3],
                    isGroup=row[4]
                )
            else:
                tempResource = ResGroup(
                    resourceId=row[0],
                    resourceName=row[1],
                    resourceType=self.allResourceTypes[row[2]],
                    contentId=row[3],
                    isGroup=row[4]
                )
            self.allResources[resId] = tempResource
        for rid, rname, isLogin in roleTable:
            role = Role(roleId=rid, roleName=rname, isLogin=isLogin)
            self.allRoles[rid] = role
        for rid, rname, isLogin in roleTable:
            childparents = self.getRoleMemberOfTable(rid)
            role = self.allRoles[rid]
            for cid, pid in childparents:
                role.addParent(self.allRoles[pid])
            roleReses = self.getRolePermissionResourceTable(rid)
            if roleReses:
                for resId in self.getResources(roleReses):
                    role.addResource(self.allResources[resId], roleReses[resId])

    def permIdToName(self, ins):
        try:
            if isinstance(ins, int):
                if ins in self.permissionTable:
                    return self.permissionTable[ins]["name"]
            return True
        except Exception as e:
            print e
            return False

    def registRole(self, role):
        try:
            if isinstance(role, Role):
                if not role.getId() in self.allRoles:
                    self.allRoles[role.getId()] = role
            return True
        except Exception as e:
            print e
            return False

    def removeRole(self, role):
        try:
            if isinstance(role, Role):
                if role.getId() in self.allRoles:
                    for roId, ro in self.allRoles.items():
                        if roId != role.getId():
                            ro.removeParent(role)
                    del self.allRoles[role.getId()]
            return True
        except Exception as e:
            print e
            return False

    def registResource(self, resources):
        try:
            if isinstance(resources, tuple) or isinstance(resources, list):
                for res in resources:
                    if isinstance(res, Resource):
                        if not res.getId() in self.allResources:
                            self.allResources[res.getId()] = res
                            self.redisdb.hset('ResourceTable', res.getName(), res.getId())

            else:
                if isinstance(resources, Resource):
                    self.allResources[resources.getId()] = resources
                    self.redisdb.hset('ResourceTable', resources.getName(), resources.getId())
            return True
        except Exception as e:
            print e
            return False

    def removeResource(self, resources):
        try:
            if isinstance(resources, tuple) or isinstance(resources, list):
                for res in resources:
                    if isinstance(res, Resource):
                        if res.getId() in self.allResources:
                            del self.allResources[res.getId()]
                            self.redisdb.hdel('ResourceTable', res.getName())
            else:
                if isinstance(resources, Resource):
                    if resources.getId() in self.allResources:
                        self.allResources[resources.getId()] = resources
                        self.redisdb.hdel('ResourceTable', resources.getName())
            return True
        except Exception as e:
            print e
            return False

    def addResourceType(self, resourceType):
        try:
            if isinstance(resourceType, ResourceType):
                if resourceType.getId() not in self.allResourceTypes:
                    self.allResourceTypes[resourceType.getId()] = resourceType
                return True
            return True
        except Exception as e:
            print e
            return False

    def removeResourceType(self, resourceTypeId):
        try:
            for rid, role in self.allRoles.items():
                for resId, resPerms in role.getResources().items():
                    resInstance = resPerms.getResource()
                    if resInstance.getResourceType().getId() == resourceTypeId:
                        del role.resources[resId]
            for resId, res in self.allResources.items():
                if res.getResourceType().getId() == resourceTypeId:
                    del self.allResources[resId]
            if resourceTypeId in self.allResourceTypes:
                del self.allResourceTypes[resourceTypeId]
            return True
        except Exception as e:
            print e
            return False

    def getResourceTypeTable(self, rtId=None):
        try:
            cur = self.db.cursor()
            if rtId is None:
                sql = '''SELECT * FROM t_resource_type;'''
                cur.execute(sql)
                if cur.rowcount == 0:
                    raise Exception('Error: visit t_resource_type failed!!!')
                return cur.fetchall()
            else:
                sql = '''SELECT * FROM t_resource_type WHERE id={0};'''.format(rtId)
                cur.execute(sql)
                if cur.rowcount == 0:
                    raise Exception('Error: visit t_resource_type failed when id = {0}!!!'.format(rtId))
                return cur.fetchone()
        except Exception as e:
            print e
            self.db.rollback()
            return False
        finally:
            cur.close()

    def getResourceTypePermissions(self, resourceTypeId):
        try:
            cur = self.db.cursor()
            if resourceTypeId is not None:
                sql = '''SELECT * FROM t_permission WHERE resource_type_id={0};'''.format(resourceTypeId)
                cur.execute(sql)
                if cur.rowcount == 0:
                    raise Exception('Error: visit t_permission failed when resourcetype id:{0}!!!'.format(resourceTypeId))
                return dict(map(lambda x: (x[0], x[1]), cur.fetchall()))
        except Exception as e:
            print e
            self.db.rollback()
            return False
        finally:
            cur.close()

    def getResources(self, resourceOfRole):
        tmpDict = {}
        for resId in resourceOfRole.keys():
            row = self.resourceTable[resId]
            tmpDict[resId] = row
            if row[4]:
                groupResourceList = self.getGroupResourceTable(resId)
                if groupResourceList and isinstance(groupResourceList, list):
                    for resId2 in groupResourceList:
                        self.allResources[resId].addMember(self.allResources[resId2])
        return tmpDict

    def getPermissionTable(self):
        cur = self.db.cursor()
        try:
            permissionTable = {}
            sql = '''SELECT * FROM t_permission'''
            cur.execute(sql)
            if cur.rowcount == 0:
                raise Exception('Error: visit t_permission failed!!!')
            for i, name, description, resourceTypeId in cur.fetchall():
                permissionTable[i] = {"id": i, "name": name, "description": description, "resourceTypeId": resourceTypeId}
            return permissionTable

        except Exception as e:
            print e
            self.db.rollback()
            return False
        finally:
            cur.close()

    def getResourceTable(self):
        try:
            cur = self.db.cursor()
            resourceTable = {}
            sql = '''SELECT * FROM t_resource'''
            cur.execute(sql)
            if cur.rowcount == 0:
                raise Exception('Error: visit t_resource failed!!!')
            tmpDict = {}
            for row in cur.fetchall():
                resourceTable[row[0]] = row
                tmpDict[row[1]] = row[0]
            self.redisdb.hmset('ResourceTable', tmpDict)
            return resourceTable
        except Exception as e:
            print e
            self.db.rollback()
            return False
        finally:
            cur.close()

    def getRedisResourceTable(self, resourceName=None):
        if resourceName:
            if self.redisdb.hexists('ResourceTable', resourceName):
                return self.redisdb.hget('ResourceTable', resourceName)
            else:
                return False
        else:
            return self.redisdb.hgetall('ResourceTable')

    def getRoleTable(self):
        try:
            cur = self.db.cursor()
            sql = '''SELECT * FROM t_role'''
            cur.execute(sql)
            if cur.rowcount == 0:
                raise Exception('Error: visit t_role failed!!!')
            return cur.fetchall()
        except Exception as e:
            print e
            self.db.rollback()
            return False
        finally:
            cur.close()

    def getRoleMemberOfTable(self, childRoleId):
        try:
            cur = self.db.cursor()
            sql = '''SELECT * FROM t_role_memberof WHERE child_role_id={0}'''.format(childRoleId)
            cur.execute(sql)
            if cur.rowcount == 0:
                raise Exception('Error: visit t_role_memberOf failed!!! when id = {0}'.format(childRoleId))
            return cur.fetchall()
        except Exception as e:
            print e
            self.db.rollback()
            return False
        finally:
            cur.close()

    def getGroupResourceTable(self, groupId):
        try:
            cur = self.db.cursor()
            sql = '''SELECT resource_id FROM t_group_resource WHERE group_id={0}'''.format(groupId)
            cur.execute(sql)
            if cur.rowcount == 0:
                raise Exception('Message: visit t_group_resource is empty when groupid={0}!!!'.format(groupId))
            return map(lambda x: x[0], cur.fetchall())
        except Exception as e:
            print e
            self.db.rollback()
            return False
        finally:
            cur.close()

    def getRolePermissionResourceTable(self, roleId):
        try:
            resourcePermissions = {}
            cur = self.db.cursor()
            sql = '''SELECT resource_id FROM t_role_permission_resource
                     WHERE role_id={0}'''.format(roleId)
            cur.execute(sql)
            tmpRes = cur.fetchall()
            if not tmpRes:
                raise Exception("no resource for role:<id: {0}>".format(roleId))
            tmpRes = map(lambda x: x[0], tmpRes)
            for i in tmpRes:

                sql = '''SELECT permission_id FROM t_role_permission_resource
                             WHERE role_id={0} AND resource_id={1}'''.format(roleId, i)
                cur.execute(sql)
                tmpPerms = map(lambda x: x[0], cur.fetchall())
                resourcePermissions[i] = tmpPerms
            return resourcePermissions
        except Exception as e:
            print e
            self.db.rollback()
            return False
        finally:
            cur.close()

if __name__ == '__main__':
    conn = psycopg2.connect(database="acl2", user="postgres", password="powerup", host="127.0.0.1", port="5432")
    import redis

    r = redis.StrictRedis(host='127.0.0.1', port=6379, db=1, password='powerup-redis')

    RM = RoleManager(conn,r)
    a = RM.allRoles[1].hasPermission(75,'ADD_RESOURCE_TYPE')
    print a





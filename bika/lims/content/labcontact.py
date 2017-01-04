# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

"""The lab staff
"""
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import manage_users
from Products.CMFCore import permissions
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.Archetypes.public import LinesField
from Products.Archetypes.public import MultiSelectionWidget
from Products.Archetypes.public import ImageField
from Products.Archetypes.public import ImageWidget
from Products.Archetypes.public import ReferenceField
from Products.Archetypes.public import ComputedField
from Products.Archetypes.public import ComputedWidget
from Products.Archetypes.public import StringField
from Products.Archetypes.public import Schema
from Products.Archetypes.public import registerType
from Products.Archetypes.public import DisplayList
from Products.Archetypes.public import ReferenceWidget
from Products.Archetypes.references import HoldingReference
from bika.lims.content.person import Person
from bika.lims.config import PROJECTNAME
from bika.lims import bikaMessageFactory as _
from bika.lims.utils import t
from zope.component import getAdapters
from zope.interface import implements
from bika.lims.interfaces import ILabContact
from bika.lims.vocabularies import CustomPubPrefVocabularyFactory
import sys

schema = Person.schema.copy() + Schema((
    LinesField('PublicationPreference',
        vocabulary_factory = 'bika.lims.vocabularies.CustomPubPrefVocabularyFactory',
        default = 'email',
        schemata = 'Publication preference',
        widget = MultiSelectionWidget(
            label=_("Publication preference"),
        ),
    ),
    ImageField('Signature',
        widget = ImageWidget(
            label=_("Signature"),
            description = _(
                "Upload a scanned signature to be used on printed analysis "
                "results reports. Ideal size is 250 pixels wide by 150 high"),
        ),
    ),
    # TODO: Department'll be delated
    ReferenceField('Department',
        required = 0,
        vocabulary_display_path_bound = sys.maxint,
        allowed_types = ('Department',),
        relationship = 'LabContactDepartment',
        vocabulary = 'getDepartments',
        referenceClass = HoldingReference,
        widget = ReferenceWidget(
            visible=False,
            checkbox_bound = 0,
            label=_("Department"),
            description=_("The laboratory department"),
        ),
    ),
    ReferenceField('Departments',
        required = 0,
        vocabulary_display_path_bound = sys.maxint,
        allowed_types = ('Department',),
        relationship = 'LabContactDepartment',
        vocabulary = '_departmentsVoc',
        referenceClass = HoldingReference,
        multiValued=1,
        widget = ReferenceWidget(
            checkbox_bound = 0,
            label=_("Departments"),
            description=_("The laboratory departments"),
        ),
    ),
    StringField('DefaultDepartment',
        required = 0,
        vocabulary_display_path_bound = sys.maxint,
        vocabulary = '_defaultDepsVoc',
        widget = ReferenceWidget(
            visible=True,
            checkbox_bound = 0,
            label=_("Default Department"),
            description=_("Default Department"),
        ),
    ),
))

schema['JobTitle'].schemata = 'default'
# Don't make title required - it will be computed from the Person's Fullname
schema['title'].required = 0
schema['title'].widget.visible = False

class LabContact(Person):
    security = ClassSecurityInfo()
    displayContentsTab = False
    schema = schema
    implements(ILabContact)

    _at_rename_after_creation = True
    def _renameAfterCreation(self, check_auto_id=False):
        from bika.lims.idserver import renameAfterCreation
        renameAfterCreation(self)

    def Title(self):
        """ Return the contact's Fullname as title """
        return safe_unicode(self.getFullname()).encode('utf-8')

    def hasUser(self):
        """ check if contact has user """
        return self.portal_membership.getMemberById(
            self.getUsername()) is not None

    # TODO: Remove getDepartment
    from bika.lims import deprecated
    @deprecated(comment="bika.lims.contant.labcontact.getDepartment "
                        "is deprecated and will be removed "
                        "in Bika LIMS 3.3. Please, use getDepartments intead")
    def getDepartment(self):
        """
        This function is a mirror for getDepartments to maintain the
        compability with the old version.
        """
        return self.getDepartments()[0] if self.getDepartments() else None

    def _departmentsVoc(self):
        """
        Returns a vocabulary object with the available departments.
        """
        bsc = getToolByName(self, 'portal_catalog')
        items = [(o.UID, o.Title) for o in
                               bsc(portal_type='Department',
                                   inactive_state = 'active')]
        # Getting the departments uids
        deps_uids = [i[0] for i in items]
        # Getting the assigned departments
        objs = self.getDepartments()
        # If one department assigned to the Lab Contact is disabled, it will
        # be shown in the list until the department has been unassigned.
        for o in objs:
            if o and o.UID() not in deps_uids:
                items.append((o.UID(), o.Title()))
        items.sort(lambda x,y: cmp(x[1], y[1]))
        return DisplayList(list(items))

    def _defaultDepsVoc(self):
        """
        Returns a vocabulary object containing all its departments.
        """
        # Getting the assigned departments
        deps=self.getDepartments()
        items=[]
        for d in deps:
            items.append((d.UID(), d.Title()))
        items.sort(lambda x,y: cmp(x[1], y[1]))
        return DisplayList(list(items))

    def addDepartment(self, dep):
        """
        It adds a new department to the departments content field.
        @dep: is a uid or a department object
        @return: True when the adding process has been done,
            False otherwise.
        """
        # check if dep is an uid
        if type(dep) is str:
            deps = self.getDepartments()
            deps = [d.UID() for d in deps]
        else:
            deps = self.getDepartments()
        if dep and dep not in deps:
            deps.append(dep)
            self.setDepartments(deps)
        return True

    def removeDepartment(self, dep):
        """
        It removes a department to the departments content field.
        @dep: is a uid or a department object
        @return: True when the removing process has been done,
            False otherwise.
        """
        # check if dep is an uid
        if type(dep) is str:
            deps = self.getDepartments()
            deps = [d.UID() for d in deps]
        else:
            deps = self.getDepartments()
        if dep and dep in deps:
            deps.remove(dep)
            self.setDepartments(deps)
        return True

    def getSortedDepartments(self):
        """
        It returns the departments the departments sorted by title.
        """
        deps = self.getDepartments()
        deps.sort(key=lambda department: department.title)
        return deps


registerType(LabContact, PROJECTNAME)

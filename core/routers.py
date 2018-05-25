from rest_framework.routers import DefaultRouter
from gtfs.views import AgencyViewSet, StopViewSet, RouteViewSet, \
    TripViewSet, CalendarViewSet, CalendarDateViewSet, \
    FareAttributeViewSet, FareRuleViewSet

router = DefaultRouter()
router.register('agency', AgencyViewSet)
router.register('stop', StopViewSet)
router.register('route', RouteViewSet)
router.register('trip', TripViewSet)
router.register('calendar', CalendarViewSet)
router.register('calendar-date', CalendarDateViewSet)
router.register('fare-attribute', FareAttributeViewSet)
router.register('fare-rule', FareRuleViewSet)

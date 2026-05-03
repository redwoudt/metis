from metis.handler.request_handler import RequestHandler
from metis.mediator import ConversationMediator
from metis.services.services import Services


def test_services_builds_conversation_mediator():
    services = Services()

    handler = RequestHandler(
        config={"vendor": "mock", "model": "stub", "policies": {}},
        services=services,
    )

    mediator = services.build_conversation_mediator(
        session_manager=handler.session_manager,
        policy=handler.policy,
        auth_policy=handler.auth_policy,
        strategy=handler.strategy,
        config=handler.config,
        request_handler=handler,
    )

    assert isinstance(mediator, ConversationMediator)
    assert mediator.services is services
    assert mediator.session_manager is handler.session_manager
    assert mediator.request_handler is handler


def test_request_handler_uses_services_to_build_mediator():
    services = Services()

    handler = RequestHandler(
        config={"vendor": "mock", "model": "stub", "policies": {}},
        services=services,
    )

    assert isinstance(handler.mediator, ConversationMediator)
    assert handler.mediator.services is services
    assert handler.mediator.session_manager is handler.session_manager
    assert handler.mediator.request_handler is handler


def test_services_get_request_handler_returns_shared_handler():
    services = Services()

    first = services.get_request_handler(
        config={"vendor": "mock", "model": "stub", "policies": {}}
    )
    second = services.get_request_handler(
        config={"vendor": "mock", "model": "stub", "policies": {}}
    )

    assert isinstance(first, RequestHandler)
    assert isinstance(second, RequestHandler)

    # Config-specific handlers are intentionally not cached.
    assert first is not second


def test_services_get_request_handler_caches_default_handler():
    services = Services()

    first = services.get_request_handler()
    second = services.get_request_handler()

    assert first is second
    assert isinstance(first, RequestHandler)
    assert first.services is services
    assert first.mediator.services is services
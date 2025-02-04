from __future__ import annotations

from sc_client import session
from sc_client.constants import common
from sc_client.constants.sc_types import ScType
from sc_client.models import Response, ScAddr, ScEvent, ScLinkContent, ScLinkContentType, ScTemplateResult


class BaseResponseProcessor:
    def __init__(self):
        pass

    def __call__(self, response: Response, *args):
        raise NotImplementedError


class CreateElementsResponseProcessor(BaseResponseProcessor):
    def __call__(self, response: Response, *_) -> list[ScAddr]:
        return [ScAddr(addr_value) for addr_value in response.get(common.PAYLOAD)]


class CheckElementsResponseProcessor(BaseResponseProcessor):
    def __call__(self, response: Response, *_) -> list[ScType]:
        return [ScType(type_value) for type_value in response.get(common.PAYLOAD)]


class DeleteElementsResponseProcessor(BaseResponseProcessor):
    def __call__(self, response: Response, *_) -> bool:
        return response.get(common.STATUS)


class SetLinkContentResponseProcessor(BaseResponseProcessor):
    def __call__(self, response: Response, *_) -> bool:
        return response.get(common.STATUS)


class GetLinkContentResponseProcessor(BaseResponseProcessor):
    def __call__(self, response: Response, *_) -> ScLinkContent:
        response_payload = response.get(common.PAYLOAD)[0]
        str_type = response_payload.get(common.TYPE)
        content_type = 0
        if str_type == common.STRING:
            content_type = ScLinkContentType.STRING.value
        elif str_type == common.INT:
            content_type = ScLinkContentType.INT.value
        elif str_type == common.BINARY:
            content_type = ScLinkContentType.BINARY.value
        elif str_type == common.FLOAT:
            content_type = ScLinkContentType.FLOAT.value
        return ScLinkContent(response_payload.get(common.VALUE), content_type)


class GetLinksByContentResponseProcessor(BaseResponseProcessor):
    def __call__(self, response: Response, *_) -> list[list[ScAddr]]:
        response_payload = response.get(common.PAYLOAD)
        if response_payload:
            return [[ScAddr(addr_value) for addr_value in addr_list] for addr_list in response_payload]
        return response_payload


class ResolveKeynodesResponseProcessor(BaseResponseProcessor):
    def __call__(self, response: Response, *_) -> list[ScAddr]:
        response_payload = response.get(common.PAYLOAD)
        if response_payload:
            return [ScAddr(addr_value) for addr_value in response_payload]
        return response


class TemplateSearchResponseProcessor(BaseResponseProcessor):
    def __call__(self, response: Response, *_) -> list[ScTemplateResult]:
        result = []
        if response.get(common.STATUS):
            response_payload = response.get(common.PAYLOAD)
            aliases = response_payload.get(common.ALIASES)
            all_addrs = response_payload.get(common.ADDRS)
            for addrs_list in all_addrs:
                addrs = [ScAddr(addr) for addr in addrs_list]
                result.append(ScTemplateResult(addrs, aliases))
        return result


class TemplateGenerateResponseProcessor(BaseResponseProcessor):
    def __call__(self, response: Response, *_) -> ScTemplateResult:
        result = None
        if response.get(common.STATUS):
            response_payload = response.get(common.PAYLOAD)
            aliases = response_payload.get(common.ALIASES)
            addrs_list = response_payload.get(common.ADDRS)
            addrs = [ScAddr(addr) for addr in addrs_list]
            result = ScTemplateResult(addrs, aliases)
        return result


class EventsCreateResponseProcessor(BaseResponseProcessor):
    def __call__(self, response: Response, *events: ScEvent) -> list[ScEvent]:
        result = []
        for count, event in enumerate(events):
            command_id = response.get(common.PAYLOAD)[count]
            sc_event = ScEvent(command_id, event.event_type, event.callback)
            session.set_event(sc_event)
            result.append(sc_event)
        return result


class EventsDestroyResponseProcessor(BaseResponseProcessor):
    def __call__(self, response: Response, *events: ScEvent) -> bool:
        for event in events:
            session.drop_event(event.id)
        return response.get(common.STATUS)


class ResponseProcessor:
    _response_request_mapper = {
        common.ClientCommand.CREATE_ELEMENTS: CreateElementsResponseProcessor(),
        common.ClientCommand.CHECK_ELEMENTS: CheckElementsResponseProcessor(),
        common.ClientCommand.DELETE_ELEMENTS: DeleteElementsResponseProcessor(),
        common.ClientCommand.KEYNODES: ResolveKeynodesResponseProcessor(),
        common.ClientCommand.GET_LINK_CONTENT: GetLinkContentResponseProcessor(),
        common.ClientCommand.GET_LINKS_BY_CONTENT: GetLinksByContentResponseProcessor(),
        common.ClientCommand.SET_LINK_CONTENTS: SetLinkContentResponseProcessor(),
        common.ClientCommand.EVENTS_CREATE: EventsCreateResponseProcessor(),
        common.ClientCommand.EVENTS_DESTROY: EventsDestroyResponseProcessor(),
        common.ClientCommand.GENERATE_TEMPLATE: TemplateGenerateResponseProcessor(),
        common.ClientCommand.SEARCH_TEMPLATE: TemplateSearchResponseProcessor(),
    }

    def run(self, request_type: common.ClientCommand, *args, **kwargs):
        response_processor = self._response_request_mapper.get(request_type)
        return response_processor(*args, **kwargs)

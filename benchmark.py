import cProfile
import logging
import os
import re
from pstats import Stats

from markov_draftjs import get_content_sample
from memory_profiler import profile

from draftjs_exporter.constants import BLOCK_TYPES, ENTITY_TYPES
from draftjs_exporter.defaults import BLOCK_MAP, STYLE_MAP
from draftjs_exporter.dom import DOM
from draftjs_exporter.html import HTML
from example import br, entity_fallback, image, list_item, ordered_list


def document(props):
    return DOM.create_element(
        "a",
        {"title": props.get("label"), "href": f"/documents/{props.get('id')}"},
        props["children"],
    )


def link(props):
    return DOM.create_element("a", {"href": props["url"]}, props["children"])


def block_fallback(props):
    type_ = props["block"]["type"]

    logging.warning(f'Missing config for "{type_}".')
    return DOM.create_element("div", {}, props["children"])


config = {
    "block_map": dict(
        BLOCK_MAP,
        **{
            BLOCK_TYPES.HEADER_TWO: "h2",
            BLOCK_TYPES.HEADER_THREE: {
                "element": "h3",
                "props": {"class": "u-text-center"},
            },
            BLOCK_TYPES.UNORDERED_LIST_ITEM: {
                "element": "li",
                "wrapper": "ul",
                "wrapper_props": {"class": "bullet-list"},
            },
            BLOCK_TYPES.ORDERED_LIST_ITEM: {
                "element": list_item,
                "wrapper": ordered_list,
            },
            BLOCK_TYPES.FALLBACK: block_fallback,
        },
    ),
    "style_map": STYLE_MAP,
    "entity_decorators": {
        ENTITY_TYPES.IMAGE: image,
        ENTITY_TYPES.LINK: link,
        ENTITY_TYPES.DOCUMENT: document,
        ENTITY_TYPES.HORIZONTAL_RULE: lambda props: DOM.create_element("hr"),
        ENTITY_TYPES.EMBED: None,
        ENTITY_TYPES.FALLBACK: entity_fallback,
    },
    "composite_decorators": [{"strategy": re.compile(r"\n"), "component": br}],
    "engine": DOM.STRING,
}

exporter = HTML(config)

content_states = get_content_sample()

BENCHMARK_RUNS = int(os.environ.get("BENCHMARK_RUNS", 1))

print(f"Exporting {len(content_states)} ContentStates {BENCHMARK_RUNS} times")

pr = cProfile.Profile()
pr.enable()

for i in range(0, BENCHMARK_RUNS):
    for content_state in content_states:
        exporter.render(content_state)

pr.disable()
p = Stats(pr)

p.strip_dirs().sort_stats("cumulative").print_stats(10)

print("Measuring memory consumption")


@profile(precision=6)
def memory_consumption_run():
    exporter = HTML(config)

    for content_state in content_states:
        exporter.render(content_state)


memory_consumption_run()

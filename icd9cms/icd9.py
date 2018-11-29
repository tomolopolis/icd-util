import itertools
import logging
import pickle
import sys
from pathlib import Path
from time import sleep
from typing import List, Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup as BSoup

__base_url = 'http://www.icd9data.com'
__root_resource = '2015/Volume1/default.htm'
__lookup_table = dict()

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s: %(message)s')
logger = logging.getLogger(__name__)


class Node:
    def __init__(self, code: str, short_desc: str, long_desc: str = None,
                 leaf: bool = False, parent=None, children=None):
        self.code = code.replace('.', '')
        self.short_desc = short_desc
        self.long_desc = long_desc
        self.is_leaf = leaf
        self.parent = parent
        self.children = children

    def __repr__(self):
        return '%s:%s:%s' % (self.code, self.short_desc, self.long_desc)

    @property
    def siblings(self) -> List:
        if self.parent is not None:
            return [c for c in self.parent.children if c is not self]

    @property
    def alt_code(self):
        if '-' in self.code or len(self.code) < 4 or \
                (self.code.startswith('E') and len(self.code) < 5):
            return self.code
        else:
            idx_for_dot = 4 if self.code.startswith('E') else 3
            return '%s.%s' % (self.code[0:idx_for_dot], self.code[idx_for_dot:])

    @property
    def leaves(self):
        def collect_leaf_nodes(node: Node) -> Iterable:
            if node.is_leaf:
                return [node]
            leaves = [collect_leaf_nodes(c) for c in node.children]
            return itertools.chain.from_iterable([l for l in leaves if l is not None])

        return collect_leaf_nodes(self)

    def ancestors(self, depth=None) -> List:
        def accu_ancestors(node, ancestors, curr_depth, max_depth) -> List:
            if node is None or \
                    (max_depth is not None and curr_depth >= max_depth):
                return ancestors
            ancestors.append(node.code)
            return accu_ancestors(node.parent, ancestors, curr_depth+1, max_depth)

        if self.parent is None:
            return []
        return accu_ancestors(self.parent, [], 0, depth)

    def descendants(self, depth=None):
        def acc_descendants(nodes, descendants, curr_depth, max_depth) -> List:
            if max_depth is not None and curr_depth >= max_depth:
                return descendants
            if nodes is not None:
                descendants.extend(n.code for n in nodes)
                for node in nodes:
                    acc_descendants(node.children, descendants, curr_depth+1, max_depth)
            return descendants

        return acc_descendants(self.children, [], 0, depth)


def _strip_elements(ul: List[BSoup]) -> List[Node]:
    """Strip non-leaf pages"""
    nodes = [Node(l.contents[0].getText(), str(l.contents[-1]).strip()) for l in ul]
    for node in nodes:
        logger.info('Created branch Node: %s: %s', node.code, node.short_desc)

    sub_links = [__base_url + l.contents[0]['href'] for l in ul]
    next_pages = [BSoup(requests.get(link).text, 'lxml') for link in sub_links]
    sleep(5)  # Don't DOS the search service
    for parent_node, page in zip(nodes, next_pages):
        child_nodes = _scrape_nodes_from_page(parent_node, page)
        parent_node.children = child_nodes
        for child in child_nodes:
            child.parent = parent_node
        __lookup_table[parent_node.code] = parent_node
    return nodes


def _strip_non_specific_codes(parent_node: Node, tags: List[BSoup]) -> List[Node]:
    lowest_branch_nodes = [Node(n.parent.find(attrs={'class': 'identifier'}).getText(),
                                n.parent.find(attrs={'class': 'threeDigitCodeListDescription'}
                                              ).getText(),
                                children=[])
                           for n in tags]

    lowest_branch_nodes = [n for n in lowest_branch_nodes if n.code != parent_node.code]
    lowest_branch_nodes = [n for n in lowest_branch_nodes if n.code != parent_node.code]
    for node in lowest_branch_nodes:
        __lookup_table[node.code] = node
    return lowest_branch_nodes


def _scrape_nodes_from_page(parent_node: Node, page: BSoup) -> List[Node]:
    el = page.find(attrs={'class': 'definitionList'})
    if el is not None:  # non-leaf tag
        if el.name == 'div':
            return _strip_elements(el.contents[0])
        elif el.name == 'ul':
            return _strip_elements(el)  # strip branch records
    else:
        # Should be leaf page now...
        return _strip_non_specific_codes(parent_node, 
                                         page.findAll(attrs={'alt': 'Non-specific code'}))


def _rebuild_lookup_table(node: Node):
    __lookup_table[node.code] = node
    if node.children is not None:
        for c in node.children:
            _rebuild_lookup_table(c)


def _load():
    path = Path(__file__).parent.joinpath('data/hierarchy.pickle')
    if path.exists():
        root_node = pickle.load(path.open('rb'))
        _rebuild_lookup_table(root_node)
        return root_node, __lookup_table
    else:
        print('Cache files not found, either they have been removed / '
              'you are running from the wrong working dir')
        print('Use icd9.scrape() to re-generate the files')


def scrape():
    icd9_root = requests.get('%s/%s' % (__base_url, __root_resource))
    root_html = BSoup(icd9_root.text, 'lxml')
    index = root_html.find('div', {'class': 'definitionList'})
    top_level = [c for c in index.contents[0].contents]
    top_level_nodes = _strip_elements(top_level)
    root_node = Node('n/a', 'root', children=top_level_nodes)

    # index for looking up codes and
    __lookup_table[root_node.code] = root_node

    import pdb
    pdb.set_trace()

    logger.info('Done scraping - save intermediate state')

    # append real child nodes to current leaf nodes
    logger.info('Add leaf elements from cms.gov download')
    icd9_codes = pd.read_excel(Path(__file__).parent.joinpath(
        'data/CMS32_DESC_LONG_SHORT_DX.xlsx'))
    for code in icd9_codes.to_records():
        diag_code = code['DIAGNOSIS CODE']
        if len(diag_code) == 3 or (diag_code.startswith('E') and len(diag_code) == 4):
            __lookup_table[diag_code].is_leaf = True
        else:
            parent_code = diag_code[:-1]
            parent_node = __lookup_table[parent_code]
            node = Node(diag_code, code['SHORT DESCRIPTION'], code['LONG DESCRIPTION'],
                        leaf=True, parent=parent_node)
            logger.info('Created leaf Node: %s: %s', node.code, node.short_desc)
            parent_node.children.append(node)
            __lookup_table[node.code] = node

    pdb.set_trace()
    pickle.dump(root_node, Path(__file__).parent.joinpath('data/hierarchy.pickle').open('wb'))
    logger.info('Successfully finished scraping - '
                'use search(code) to find codes and associated hierarchies')


def search(code: str):
    if len(__lookup_table) < 1:
        _load()
    if code is None:
        return __lookup_table.get('n/a')
    return __lookup_table.get(code.replace('.', ''))

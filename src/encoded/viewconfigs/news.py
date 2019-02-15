"""
# News View
Some Desc

## Inheritance
NewsView<-SearchView<-BaseView

### SearchView function dependencies
- validate_items
### BaseView function dependencies
- _format_facets
"""
from collections import OrderedDict

from encoded.helpers.helper import format_results

from snovault.helpers.helper import (  # pylint: disable=import-error
    get_filtered_query,
    get_search_fields,
    list_result_fields,
    set_filters,
    set_facets,
)
from snovault.viewconfigs.searchview import SearchView  # pylint: disable=import-error

import time
import logging
import datetime

class NewsView(SearchView):  # pylint: disable=too-few-public-methods
    '''News View'''
    _view_name = 'summary'
    _factory_name = None
    def __init__(self, context, request):
        super(NewsView, self).__init__(context, request)
        self._from_ = 0
        self._size = 25
        self._es_index = 'page'
        
        # Create the Logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
 
        # Create the Handler for logging data to a file
        logger_handler = logging.FileHandler('search_test_1.log')
        logger_handler.setLevel(logging.DEBUG)
 
        # Create a Formatter for formatting the log messages
        logger_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
 
        # Add the Formatter to the Handler
        logger_handler.setFormatter(logger_formatter)
 
        # Add the Handler to the Logger
        self.logger.addHandler(logger_handler)
        self.logger.info('Completed configuring logger()!')
        self.logger.debug('------------------')
        self.logger.debug(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.logger.debug('------------------')

    def preprocess_view(self):
        '''
        Main function to construct query and build view results json
        * Only publicly accessible function
        '''
        t_start = time.time()
        self._result['@id'] = '/news/' + self._search_base
        self._result['@type'] = ['News']
        self._result['notification'] = ''
        doc_types = ['Page']
        search_fields, _ = get_search_fields(self._request, doc_types)
        t_end = time.time()
        self.logger.debug('{} time: {:.20f}'.format(
            'ENCODED news preprocess_view _____a',
            (t_end - t_start)*1000
        ))
        query = get_filtered_query(
            '*',
            search_fields,
            sorted(list_result_fields(self._request, doc_types)),
            self._principals,
            doc_types
        )
        self.logger.debug('{} time: {:.20f}'.format(
            'ENCODED news preprocess_view _____b',
            (t_end - t_start)*1000
        ))
        del query['query']['query_string']
        sort = OrderedDict()
        result_sort = OrderedDict()
        sort['embedded.date_created'] = result_sort['date_created'] = {
            'order': 'desc',
            'unmapped_type': 'keyword',
        }
        self.logger.debug('{} time: {:.20f}'.format(
            'ENCODED news preprocess_view _____c',
            (t_end - t_start)*1000
        ))
        query['sort'] = result_sort
        self._result['sort'] = result_sort
        used_filters = set_filters(
            self._request,
            query,
            self._result,
            [('type', 'Page'), ('news', 'true'), ('status', 'released')]
        )
        self.logger.debug('{} time: {:.20f}'.format(
            'ENCODED news preprocess_view _____d',
            (t_end - t_start)*1000
        ))
        facets = []
        if len(doc_types) == 1 and 'facets' in self._types[doc_types[0]].schema:
            facets.extend(self._types[doc_types[0]].schema['facets'].items())
        query['aggs'] = set_facets(facets, used_filters, self._principals, doc_types)
        es_results = self._elastic_search.search(
            body=query,
            index=self._es_index,
            doc_type=self._es_index,
            from_=0,
            size=25)
        self.logger.debug('{} time: {:.20f}'.format(
            'ENCODED news preprocess_view _____e',
            (t_end - t_start)*1000
        ))
        total = es_results['hits']['total']
        if not total:
            self._request.response.status_code = 404
            self._result['notification'] = 'No results found'
            self._result['@graph'] = []
            return self._result
        self._result['notification'] = 'Success'
        self._result['total'] = total
        graph = format_results(
            self._request,
            es_results['hits']['hits'],
            self._result
        )
        self._result['@graph'] = list(graph)
        self.logger.debug('{} time: {:.20f}'.format(
            'ENCODED news preprocess_view _____f',
            (t_end - t_start)*1000
        ))
        schemas = [
            self._types[doc_type].schema
            for doc_type in doc_types
        ]
        self._result['facets'] = self._format_facets(
            es_results,
            facets,
            used_filters,
            schemas,
            total,
            self._principals
        )
        self.logger.debug('{} time: {:.20f}'.format(
            'ENCODED news preprocess_view _____g',
            (t_end - t_start)*1000
        ))

        t_end = time.time()
        self.logger.debug('{} time: {:.20f}'.format(
            'ENCODED news preprocess_view',
            (t_end - t_start)*1000
        ))
        return self._result

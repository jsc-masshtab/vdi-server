import {NgModule} from '@angular/core';
import {ApolloModule, APOLLO_OPTIONS} from 'apollo-angular';
import {HttpLinkModule, HttpLink} from 'apollo-angular-link-http';
import {InMemoryCache} from 'apollo-cache-inmemory';

const uri = 'http://192.168.8.10/admin';

export function createApollo(httpLink: HttpLink) {
  return {
    link: httpLink.create({uri, includeQuery: true, includeExtensions: false }),
    cache: new InMemoryCache({ addTypename: false, dataIdFromObject: object =>  object.id }),
    defaultOptions: {
      watchQuery: {
          fetchPolicy: 'network-only' // обойдет кеш и напрямую отправит запрос на сервер.
      },
      query: {
          fetchPolicy: 'network-only'
      },
      mutate: {
          fetchPolicy: 'no-cache'
      }
    }
  };
}

@NgModule({
  exports: [ApolloModule, HttpLinkModule],
  providers: [
    {
      provide: APOLLO_OPTIONS,
      useFactory: createApollo,
      deps: [HttpLink]
    }
  ]
})
export class GraphQLModule {}

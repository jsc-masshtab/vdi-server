import { environment } from './../environments/environment';
import {NgModule} from '@angular/core';
import {ApolloModule, APOLLO_OPTIONS} from 'apollo-angular';
import { ApolloLink } from 'apollo-link';
import {HttpLinkModule, HttpLink } from 'apollo-angular-link-http';
import {InMemoryCache} from 'apollo-cache-inmemory';
import { onError } from 'apollo-link-error';
import { HttpErrorResponse } from '@angular/common/http';
import { ErrorsService } from './common/components/errors/errors.service';


const uri = environment.url;

 
export function createApollo(httpLink: HttpLink) {
  return {
    link: ApolloLink.from([
      this.errorLink,
      httpLink.create({ uri, includeQuery: true, includeExtensions: false })
    ]),
    cache: new InMemoryCache({ addTypename: false, dataIdFromObject: object =>  object.id }),
    defaultOptions: {
      watchQuery: {
        fetchPolicy: 'network-only', // обойдет кеш и напрямую отправит запрос на сервер.
        errorPolicy: 'all'
      },
      query: {
        fetchPolicy: 'network-only',
        errorPolicy: 'all'
      },
      mutate: {
        fetchPolicy: 'no-cache',
        errorPolicy: 'all'
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
    },
    ErrorsService
  ]
})
export class GraphQLModule {
  private errorLink;

  constructor(private errorsService: ErrorsService) {

    this.errorLink = onError(({ graphQLErrors, networkError }) => {
      if (graphQLErrors)
        graphQLErrors.map(({ message, locations, path }) =>
          console.log(
            `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`,
          ),
        );
        if (networkError) {
          console.log(networkError['error']['errors'],networkError instanceof HttpErrorResponse);
    
        }
      });

    console.log(this.errorsService);
  }


}

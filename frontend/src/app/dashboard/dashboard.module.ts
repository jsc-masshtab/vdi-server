import { DashboardRoutingModule } from './dashboard-routing.module';
import { CommonModule } from '@angular/common';
import { ErrorsService } from './../errors/errors.service';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { DashboardComponent } from './dashboard.component';
import { FooterComponent } from './common/components/single/footer/footer.component';
import { MainMenuComponent } from './common/components/single/main-menu/main-menu.component';
import { WaitComponent } from './common/components/single/wait/wait.component';

import { WebsocketPoolService } from './common/classes/websockPool.service';
import { WebsocketService } from './common/classes/websock.service';

import { UsersModule } from './settings/users/users.module';
import { ControllersModule } from './settings/controllers/controllers.module';
import { TemplatesModule } from './resourses/templates/templates.module';
import { NodesModule } from './resourses/nodes/nodes.module';
import { DatapoolsModule } from './resourses/datapools/datapools.module';
import { ClustersModule } from './resourses/clusters/clusters.module';
import { PoolsModule } from './pools/pools.module';
import { VmsModule } from './resourses/vms/vms.module';

import {  HttpLink } from 'apollo-angular-link-http';
import {  Apollo  } from 'apollo-angular';
import { ApolloLink, from } from 'apollo-link';
import { HttpHeaders } from '@angular/common/http';

import { NgModule } from '@angular/core';


import { WaitService } from './common/components/single/wait/wait.service';

/*  -----------------------------------   material   --------------------------------------*/
import { MAT_DIALOG_DEFAULT_OPTIONS } from '@angular/material';

/*  -----------------------------------   material   --------------------------------------*/

import { onError } from 'apollo-link-error';
import { InMemoryCache } from 'apollo-cache-inmemory';
import { environment } from 'src/environments/environment';
import { EventsModule } from './log/events/events.module';



@NgModule({
  declarations: [
    DashboardComponent,
    WaitComponent,
    MainMenuComponent,
    FooterComponent
  ],
  imports: [
    CommonModule,
    DashboardRoutingModule,
    FontAwesomeModule,

    PoolsModule,
    ClustersModule,
    DatapoolsModule,
    NodesModule,
    TemplatesModule,
    VmsModule,
    ControllersModule,
    UsersModule,
    EventsModule
  ],
  providers:
    [
     { provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: { hasBackdrop: true, restoreFocus: true } },
      WaitService,
      WebsocketService,
      WebsocketPoolService
    ]
})


export class DashboardModule {


  constructor(private apollo: Apollo,
              private httpLink: HttpLink,
              private errorService: ErrorsService,
               private waitService: WaitService
              ) {


    const url = environment.url;
    // const headers = new HttpHeaders().set('Authorization', localStorage.getItem('token') || null);

    const link = this.httpLink.create( { uri(operation) {
      let urlKnock: string = '';
      switch (operation.operationName) {
        case 'controllers':
          urlKnock = `${url + 'controllers'}`;
          break;
        case 'pools':
          urlKnock = `${url + 'pools'}`;
          break;
        case 'resources':
          urlKnock = `${url + 'resources'}`;
          break;
        case 'vms':
          urlKnock = `${url + 'vms'}`;
          break;
        case 'users':
          urlKnock = `${url + 'users'}`;
          break;
        case 'events':
          urlKnock = `${url + 'events'}`;
          break;
        default:
          urlKnock = `${url}`;
      }
      return urlKnock;
    }, includeQuery: true, includeExtensions: false } );

    const errorLink = onError(({ graphQLErrors, networkError }) => {
      if (graphQLErrors) {
        this.waitService.setWait(false);
        graphQLErrors.map(({ message, locations, path }) => {
          this.errorService.setError(message);
          console.log(`[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`, locations);
        });
      }

      if (networkError) {
        console.log(networkError, 'networkError');
        this.waitService.setWait(false);
        this.errorService.setError(networkError['message']);
      }
    });

    const authMiddleware = new ApolloLink((operation, forward) => {
      // add the authorization to the headers
      operation.setContext({
        headers: new HttpHeaders().set('Authorization', localStorage.getItem('token') || null)
      });

      return forward(operation);
    });

    this.apollo.create({
      link: from([authMiddleware, errorLink, link]),
      cache: new InMemoryCache({ addTypename: false, dataIdFromObject: object => object.id }),
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
          errorPolicy: 'all'
        }
      }
    });
  }
}

// queryDeduplication

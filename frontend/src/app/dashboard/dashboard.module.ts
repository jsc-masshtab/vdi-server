import { GroupsModule } from './settings/groups/groups.module';
import { HeaderUserComponent } from './common/components/single/header-user/header-user.component';
import { AuthStorageService } from './../login/authStorage.service';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { CommonModule } from '@angular/common';
import { ErrorsService } from './../errors/errors.service';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { DashboardComponent } from './dashboard.component';
import { FooterComponent } from './common/components/single/footer/footer.component';
import { MainMenuComponent } from './common/components/single/main-menu/main-menu.component';
import { WaitComponent } from './common/components/single/wait/wait.component';
import { UsersModule } from './settings/users/users.module';
import { AuthenticationDirectoryModule } from './settings/auth-directory/auth-directory.module';
import { ControllersModule } from './settings/controllers/controllers.module';
import { TemplatesModule } from './resourses/templates/templates.module';
import { NodesModule } from './resourses/nodes/nodes.module';
import { DatapoolsModule } from './resourses/datapools/datapools.module';
import { ClustersModule } from './resourses/clusters/clusters.module';
import { PoolsModule } from './pools/pools.module';
import { VmsModule } from './resourses/vms/vms.module';
import { EventsModule } from './log/events/events.module';


import {  HttpLink } from 'apollo-angular-link-http';
import {  Apollo  } from 'apollo-angular';
import { ApolloLink, from } from 'apollo-link';
import { HttpHeaders, HttpClientModule } from '@angular/common/http';

import { NgModule } from '@angular/core';


import { WaitService } from './common/components/single/wait/wait.service';

/*  -----------------------------------   material   --------------------------------------*/
import { MAT_DIALOG_DEFAULT_OPTIONS } from '@angular/material';
/*  -----------------------------------   material   --------------------------------------*/

import { onError } from 'apollo-link-error';
import { InMemoryCache } from 'apollo-cache-inmemory';
import { environment } from 'src/environments/environment';
import { LicenseModule } from './settings/license/license.module';

@NgModule({
  declarations: [
    DashboardComponent,
    WaitComponent,
    MainMenuComponent,
    FooterComponent,
    HeaderUserComponent
  ],
  imports: [
    CommonModule,
    DashboardRoutingModule,
    FontAwesomeModule,
    HttpClientModule,
    PoolsModule,
    ClustersModule,
    DatapoolsModule,
    NodesModule,
    TemplatesModule,
    VmsModule,
    ControllersModule,
    UsersModule,
    AuthenticationDirectoryModule,
    EventsModule,
    GroupsModule,
    LicenseModule
  ],
  providers:
    [
     { provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: { hasBackdrop: true, restoreFocus: true } }
    ]
})


export class DashboardModule {


  constructor(private apollo: Apollo,
              private httpLink: HttpLink,
              private errorService: ErrorsService,
              private waitService: WaitService,
              private authStorageService: AuthStorageService
            ) {

    const url = environment.url;

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
        case 'auth_dirs':
          urlKnock = `${url + 'auth_dirs'}`;
          break;
        case 'groups':
          urlKnock = `${url + 'groups'}`;
          break;
        case 'events':
          urlKnock = `${url + 'events'}`;
          break;
        default:
          urlKnock = `${url}`;
      }
      return urlKnock;
    }, includeQuery: true, includeExtensions: false } );

    const authMiddleware = new ApolloLink((operation, forward) => {
      operation.setContext({
        headers: new HttpHeaders().set('Authorization', `jwt ${this.authStorageService.getItemStorage('token')}`)
                  .set('Client-Type', 'angular-web')
      });
      return forward(operation);
    });

    const errorLink = onError(({ graphQLErrors, networkError, operation, forward}) => {
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
        if (networkError['status'] === 401) {
          if (networkError['error'] && networkError['error']['errors']) {
            this.errorService.setError(networkError['error']['errors']);
            return;
          }
        }
        this.errorService.setError(networkError['message']);
      }

      if (operation.variables.method === 'POST') {
        return forward(operation).filter(item => item.errors === undefined);
      }
    });


    this.apollo.create({
      link: from([errorLink, authMiddleware, link]),
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

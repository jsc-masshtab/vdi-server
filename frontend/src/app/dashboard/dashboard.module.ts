import { GroupsModule } from './pages/settings/groups/groups.module';

import { AuthStorageService } from './../login/authStorage.service';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { CommonModule } from '@angular/common';
import { ErrorsService } from './../errors/errors.service';
import { DashboardComponent } from './dashboard.component';

import { UsersModule } from './pages/settings/users/users.module';
import { AuthenticationDirectoryModule } from './pages/settings/auth-directory/auth-directory.module';
import { ControllersModule } from './pages/controllers/controllers.module';

import { PoolsModule } from './pages/pools/pools.module';

import { EventsModule } from './pages/log/events/events.module';
import { TasksModule } from './pages/log/tasks/tasks.module';


import { HttpLink } from 'apollo-angular-link-http';
import { Apollo } from 'apollo-angular';
import { ApolloLink, from } from 'apollo-link';
import { HttpHeaders, HttpClientModule } from '@angular/common/http';

import { NgModule } from '@angular/core';


import { WaitService } from './core/components/wait/wait.service';

/*  -----------------------------------   material   --------------------------------------*/
import { MAT_DIALOG_DEFAULT_OPTIONS } from '@angular/material/dialog';
/*  -----------------------------------   material   --------------------------------------*/

import { onError } from 'apollo-link-error';
import { InMemoryCache } from 'apollo-cache-inmemory';
import { environment } from 'src/environments/environment';
import { LicenseModule } from './pages/settings/license/license.module';
import { throwError } from 'rxjs';
import { ThinClientsModule } from './pages/thin-clients/thin-clients.module';
import { LogSettingModule } from './pages/log/log-setting/log-setting.module';
import { VeilEventsModule } from './pages/log/veil-events/veil-events.module';
import { ClustersModule } from './pages/resourses/clusters/clusters.module';
import { DatapoolsModule } from './pages/resourses/datapools/datapools.module';
import { NodesModule } from './pages/resourses/nodes/nodes.module';
import { ResourcePoolsModule } from './pages/resourses/resource_pools/resource_pools.module';
import { TemplatesModule } from './pages/resourses/templates/templates.module';
import { VmsModule } from './pages/resourses/vms/vms.module';
import { CoreModule } from './core/core.module';


@NgModule({
  declarations: [
    DashboardComponent,

  ],
  imports: [
    CommonModule,
    CoreModule,
    DashboardRoutingModule,
    HttpClientModule,
    PoolsModule,
    ClustersModule,
    ResourcePoolsModule,
    DatapoolsModule,
    NodesModule,
    TemplatesModule,
    VmsModule,
    ControllersModule,
    UsersModule,
    AuthenticationDirectoryModule,
    EventsModule,
    VeilEventsModule,
    TasksModule,
    LogSettingModule,
    GroupsModule,
    LicenseModule,
    ThinClientsModule
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

    const url = environment.api;

    const link = this.httpLink.create( { uri(operation) {
      return url + operation.operationName;
    }, includeQuery: true, includeExtensions: false } );

    const authMiddleware = new ApolloLink((operation, forward) => {
      operation.setContext({
        headers: new HttpHeaders().set('Authorization', `jwt ${this.authStorageService.getItemStorage('token')}`)
                  .set('Client-Type', 'angular-web')
      });
      return forward(operation);
    });

    const errorLink = onError(({ graphQLErrors, networkError, operation, forward}): any => {
      if (graphQLErrors) {

        this.waitService.setWait(false);

        graphQLErrors.map(({ message, locations, path }) => {
          console.error(`[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`, locations);
        });

        graphQLErrors.forEach((error) => {
          this.errorService.setError(error.message)
        })
      }

      if (networkError) {
        console.error(networkError, 'networkError');

        if (networkError['error'] && networkError['error']['errors']) {
          networkError['error']['errors'].forEach(er => {
            console.warn(er.message);
          });
        }

        this.waitService.setWait(false);

        if (networkError['status'] === 401) {
          if (networkError['error'] && networkError['error']['errors']) {
            this.errorService.setError(networkError['error']['errors']);
          }
        }

        this.errorService.setError(networkError['message']);
      }

      if (operation.variables.method === 'POST') {

        const context = operation.getContext();
        const body = context.response.body;

        if (body.errors) {
          return throwError({ message: 'Bad response' });
        } else {
          return forward(operation);
        }
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

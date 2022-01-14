
import { CommonModule } from '@angular/common';
import { HttpHeaders, HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { MAT_DIALOG_DEFAULT_OPTIONS } from '@angular/material/dialog';
import { Apollo } from 'apollo-angular';
import { HttpLink } from 'apollo-angular-link-http';
import { defaultDataIdFromObject, InMemoryCache } from 'apollo-cache-inmemory';
import { ApolloLink, from } from 'apollo-link';
import { onError } from 'apollo-link-error';
import { environment } from 'environments/environment';
import { throwError } from 'rxjs';

import { ErrorsService } from '@core/components/errors/errors.service';
import { WaitService } from '@core/components/wait/wait.service';
import { CoreModule } from '@core/core.module';

import { ControllersModule } from '../controllers/controllers.module';
import { EventsModule } from '../log/events/events.module';
import { LogSettingModule } from '../log/log-setting/log-setting.module';
import { TasksModule } from '../log/tasks/tasks.module';
import { VeilEventsModule } from '../log/veil-events/veil-events.module';
import { AuthStorageService } from '../login/authStorage.service';
import { PoolsModule } from '../pools/pools.module';
import { ClustersModule } from '../resourses/clusters/clusters.module';
import { DatapoolsModule } from '../resourses/datapools/datapools.module';
import { NodesModule } from '../resourses/nodes/nodes.module';
import { ResourcePoolsModule } from '../resourses/resource_pools/resource_pools.module';
import { TemplatesModule } from '../resourses/templates/templates.module';
import { VmsModule } from '../resourses/vms/vms.module';
import { AuthenticationDirectoryModule } from '../settings/auth-directory/auth-directory.module';
import { GroupsModule } from '../settings/groups/groups.module';
import { LicenseModule } from '../settings/license/license.module';
import { ServicePageModule } from '../settings/service-page/service-page.module';
import { UsersModule } from '../settings/users/users.module';
import { ThinClientsModule } from '../thin-clients/thin-clients.module';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { DashboardComponent } from './dashboard.component';
import { SystemModule } from '../settings/system/system.module';
import { SmtpModule } from '../settings/smtp/smtp.module';
import { CacheModule } from '../settings/cache/cache.module';
import { StatisticsModule } from '../log/statistics/statistics.module';


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
    ThinClientsModule,
    SystemModule,
    ServicePageModule,
    SmtpModule,
    CacheModule,
    StatisticsModule
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
      cache: new InMemoryCache({ addTypename: false, dataIdFromObject: object => defaultDataIdFromObject(object) }),
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

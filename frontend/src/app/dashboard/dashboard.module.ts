
import { CommonModule } from '@angular/common';
import { HttpHeaders, HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { MAT_DIALOG_DEFAULT_OPTIONS } from '@angular/material/dialog';
import { Apollo } from 'apollo-angular';
import { HttpLink } from 'apollo-angular/http'
import { InMemoryCache, from, ApolloLink } from '@apollo/client/core';
import { onError } from '@apollo/client/link/error';
import { environment } from 'environments/environment';
import { throwError } from 'rxjs';

import { ErrorsService } from '@core/components/errors/errors.service';
import { WaitService } from '@core/components/wait/wait.service';
import { CoreModule } from '@core/core.module';

import { ControllersModule } from '@pages/controllers/controllers.module';
import { EventsModule } from '@pages/log/events/events.module';
import { LogSettingModule } from '@pages/log/log-setting/log-setting.module';
import { TasksModule } from '@pages/log/tasks/tasks.module';
import { VeilEventsModule } from '@pages/log/veil-events/veil-events.module';
import { AuthStorageService } from '@pages/login/authStorage.service';
import { PoolsModule } from '@pages/pools/pools.module';
import { ClustersModule } from '@pages/resourses/clusters/clusters.module';
import { DatapoolsModule } from '@pages/resourses/datapools/datapools.module';
import { NodesModule } from '@pages/resourses/nodes/nodes.module';
import { ResourcePoolsModule } from '@pages/resourses/resource_pools/resource_pools.module';
import { TemplatesModule } from '@pages/resourses/templates/templates.module';
import { VmsModule } from '@pages/resourses/vms/vms.module';
import { AuthenticationDirectoryModule } from '@pages/settings/auth-directory/auth-directory.module';
import { GroupsModule } from '@pages/settings/groups/groups.module';
import { LicenseModule } from '@pages/settings/license/license.module';
import { ServicePageModule } from '@pages/settings/service-page/service-page.module';
import { UsersModule } from '@pages/settings/users/users.module';
import { ThinClientsModule } from '@pages/thin-clients/thin-clients.module';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { DashboardComponent } from './dashboard.component';
import { SystemModule } from '@pages/settings/system/system.module';
import { SmtpModule } from '@pages/settings/smtp/smtp.module';
import { CacheModule } from '@pages/settings/cache/cache.module';
import { StatisticsModule } from '@pages/statistics/statistics.module';
import { PoolStatisticsModule } from '@app/pages/statistics/pools-statistics/pool-statistics.module';
import { MAT_DATE_LOCALE } from '@angular/material/core';
import { MainModule } from '@app/pages/main/main.module';

@NgModule({
  declarations: [
    DashboardComponent,
  ],
  imports: [
    CommonModule,
    CoreModule,
    DashboardRoutingModule,
    HttpClientModule,
    MainModule,
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
    StatisticsModule,
    PoolStatisticsModule
  ],
  providers:
    [
      { provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: { hasBackdrop: true, restoreFocus: true } },
      { provide: MAT_DATE_LOCALE, useValue: 'ru-RU' }
    ]
})

export class DashboardModule {
  constructor(
    private apollo: Apollo,
    private httpLink: HttpLink,
    private errorService: ErrorsService,
    private waitService: WaitService,
    private authStorageService: AuthStorageService
  ){

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

    const cleanTypeName = new ApolloLink((operation, forward) => {
      if (operation.variables) {
        const omitTypename = (key, value) => (key === '__typename' ? undefined : value);
        operation.variables = JSON.parse(JSON.stringify(operation.variables), omitTypename);
      }

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

        if (networkError['error'] && networkError['error']['errors']) {
          this.errorService.setError(networkError['error']['errors']);
        }

        this.waitService.setWait(false);

        if (networkError['status'] === 401) {
          if (networkError['error'] && networkError['error']['errors']) {
            this.errorService.setError(networkError['error']['errors']);
          }
        }
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
      link: from([errorLink, authMiddleware, cleanTypeName, link]),
      cache: new InMemoryCache(
        {
          typePolicies: {
            Query: {
              fields: {
                thin_clients: {
                  merge( _ = [], incoming: any[]) {
                    return [...incoming];
                  }
                }
              }
            },
            PoolType: {
              merge: true
            },
            SysInfoGrapheneType: {
              merge: true
            }
          }
        }
      ),
      defaultOptions: {
        watchQuery: {
          fetchPolicy: 'cache-and-network',
          nextFetchPolicy: "cache-first",
          errorPolicy: 'ignore',
        },
        query: {
          fetchPolicy: 'network-only',
          errorPolicy: 'all',
        },
        mutate: {
          errorPolicy: 'all'
        }
      }
    });
  }
}

// queryDeduplication

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
import { ControllersModule } from './pages/controllers/controllers.module';

import { PoolsModule } from './pages/pools/pools.module';

import { EventsModule } from './log/events/events.module';
import { TasksModule } from './log/tasks/tasks.module';


import { HttpLink } from 'apollo-angular-link-http';
import { Apollo } from 'apollo-angular';
import { ApolloLink, from } from 'apollo-link';
import { HttpHeaders, HttpClientModule } from '@angular/common/http';

import { NgModule } from '@angular/core';


import { WaitService } from './common/components/single/wait/wait.service';

/*  -----------------------------------   material   --------------------------------------*/
import { MAT_DIALOG_DEFAULT_OPTIONS } from '@angular/material/dialog';
/*  -----------------------------------   material   --------------------------------------*/

import { onError } from 'apollo-link-error';
import { InMemoryCache } from 'apollo-cache-inmemory';
import { environment } from 'src/environments/environment';
import { LicenseModule } from './settings/license/license.module';
import { throwError } from 'rxjs';
import { ThinClientsModule } from './thin-clients/thin-clients.module';
import { LogSettingModule } from './log/log-setting/log-setting.module';
import { VeilEventsModule } from './log/veil-events/veil-events.module';
import { ClustersModule } from './resourses/clusters/clusters.module';
import { DatapoolsModule } from './resourses/datapools/datapools.module';
import { NodesModule } from './resourses/nodes/nodes.module';
import { ResourcePoolsModule } from './resourses/resource_pools/resource_pools.module';
import { TemplatesModule } from './resourses/templates/templates.module';
import { VmsModule } from './resourses/vms/vms.module';


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

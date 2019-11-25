import { WebsocketPoolService } from './common/classes/websockPool.service';
import { WebsocketService } from './common/classes/websock.service';

import { UsersModule } from './settings/users/users.module';
import { ControllersModule } from './settings/controllers/controllers.module';
import { TemplatesModule } from './resourses/templates/templates.module';
import { NodesModule } from './resourses/nodes/nodes.module';
import { DatapoolsModule } from './resourses/datapools/datapools.module';
import { ClustersModule } from './resourses/clusters/clusters.module';
import { PoolsModule } from './pools/pools.module';
import { SharedModule } from './common/shared.module';
import { VmsModule } from './resourses/vms/vms.module';

import { HttpLinkModule, HttpLink } from 'apollo-angular-link-http';
import { ApolloModule, Apollo } from 'apollo-angular';
import { ErrorsService } from './common/components/single/errors/errors.service';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { NgModule } from '@angular/core';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HttpClientModule } from '@angular/common/http';

/*  -----------------------------------   icons   --------------------------------------*/
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faDesktop, faDatabase, faBuilding, faLayerGroup, faPlusCircle, faSpinner, faServer, faCog, faChevronUp, faTimesCircle,
         faFolderOpen, faStar, faMinusCircle, faTv, faSyncAlt, faTrashAlt, faUsers, faMeh,
         faChartBar, faUser, faStopCircle, faPlayCircle, faPauseCircle, faEdit, faQuestionCircle, faCheckSquare,
          faExclamationTriangle, faHeartbeat, faChevronCircleUp, faComment
        } from '@fortawesome/free-solid-svg-icons';
/*  -----------------------------------   icons   --------------------------------------*/

import { MainMenuComponent } from './common/components/single/main-menu/main-menu.component';
import { ErrorsComponent } from './common/components/single/errors/errors.component';
import { FooterComponent } from './common/components/single/footer/footer.component';
import { WaitComponent } from './common/components/single/wait/wait.component';
import { WaitService } from './common/components/single/wait/wait.service';

/*  -----------------------------------   material   --------------------------------------*/
import { MAT_DIALOG_DEFAULT_OPTIONS } from '@angular/material';

/*  -----------------------------------   material   --------------------------------------*/

import { onError } from 'apollo-link-error';
import { InMemoryCache } from 'apollo-cache-inmemory';
import { environment } from 'src/environments/environment';



@NgModule({
  declarations: [
    AppComponent,
    MainMenuComponent,
    ErrorsComponent,
    FooterComponent,
    WaitComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    HttpClientModule,
    ApolloModule,
    HttpLinkModule,
    FontAwesomeModule,

    SharedModule,

    PoolsModule,
    ClustersModule,
    DatapoolsModule,
    NodesModule,
    TemplatesModule,
    VmsModule,
    ControllersModule,
    UsersModule
  ],
  entryComponents: [],
  providers:
    [
     { provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: { hasBackdrop: true, restoreFocus: true } },
      ErrorsService,
      WaitService,
      WebsocketService,
      WebsocketPoolService
    ],
  bootstrap: [AppComponent]
})


export class AppModule {


  constructor(private apollo: Apollo,
              private httpLink: HttpLink,
              private errorService: ErrorsService,
              private waitService: WaitService,
              private ws: WebsocketService
              ) {

    library.add(faDesktop, faDatabase, faLayerGroup, faPlusCircle, faMinusCircle, faSpinner, faServer, faCog, faChevronUp, faTimesCircle,
                faFolderOpen, faStar, faTv, faSyncAlt, faBuilding, faTrashAlt, faUsers, faMeh, faChartBar, faUser,
                faStopCircle, faPlayCircle, faPauseCircle, faEdit, faQuestionCircle, faCheckSquare, faExclamationTriangle, faHeartbeat,
                faChevronCircleUp, faComment);

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
        default:
          urlKnock = `${url}`;
      }
      return urlKnock;
    }, includeQuery: true, includeExtensions: false} );

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
        this.errorService.setError(networkError['message']);
        this.waitService.setWait(false);
      }
    });

    this.apollo.create({
      link: errorLink.concat(link),
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

    setTimeout(() => this.ws.init(), 1000);
  }
}

import { WaitService } from './common/components/wait/wait.service';
import { WaitComponent } from './common/components/wait/wait.component';
import { AddVMStaticPoolComponent } from './polls/add-vms/add-vms.component';
import { HttpLinkModule, HttpLink } from 'apollo-angular-link-http';
import { ApolloModule, Apollo } from 'apollo-angular';
import { ErrorsService } from './common/components/errors/errors.service';
import { AddUserComponent } from './settings/users/add-user/add-user.component';
import { VmsComponent } from './resourses/vms/vms.component';
import { VmsService } from './resourses/vms/vms.service';
import { TemplatesComponent } from './resourses/templates/templates.component';
import { RemoveControllerComponent } from './settings/controllers/remove-controller/remove-controller.component';
import { PoolDetailsComponent } from './polls/pool-details/pool-details.component';
import { NodeDetailsComponent } from './resourses/nodes/node-details/node-details.component';
import { DatapoolsService } from './resourses/datapools/datapools.service';
import { DatapoolsComponent } from './resourses/datapools/datapools.component';

import { ControllersComponent } from './settings/controllers/controllers.component';

import { ClustersService } from './resourses/clusters/clusters.service';
import { ClustersComponent } from './resourses/clusters/clusters.component';

import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HttpClientModule } from '@angular/common/http';



/*  -----------------------------------   icons   --------------------------------------*/
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faDesktop,faDatabase,faBuilding, faLayerGroup,faPlusCircle,faSpinner,faServer,faCog,faChevronUp,faTimesCircle,faFolderOpen,faStar,faMinusCircle, faTv,faSyncAlt,faTrashAlt,faUsers,faMeh,faChartBar} from '@fortawesome/free-solid-svg-icons';
/*  -----------------------------------   icons   --------------------------------------*/


import { MainMenuComponent } from './main-menu/main-menu.component';
import { BaSelect } from './common/components/baSelect';


import { TableComponentComponent } from './common/components/table-component/table-component.component';
import { ErrorsComponent } from './common/components/errors/errors.component';
import { PoolAddComponent } from './polls/pool-add/pool-add.component';
import { PoolsService } from './polls/pools.service';
import { FocusMeDirective } from './common/other/directives/focusMe.directive';
import { TableIntoComponent } from './common/components/table-into-component/table-into';
import { NodesComponent } from './resourses/nodes/nodes.component';
import { NodesService } from './resourses/nodes/nodes.service';



/*  -----------------------------------   material   --------------------------------------*/
import { MAT_DIALOG_DEFAULT_OPTIONS, ErrorStateMatcher, ShowOnDirtyErrorStateMatcher } from '@angular/material';
import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import { AddControllerComponent } from './settings/controllers/add-controller/add-controller.component';
import { ControllersService } from './settings/controllers/controllers.service';
import { FooterComponent } from './footer/footer.component';
import { ClusterDetailsComponent } from './resourses/clusters/cluster-details/cluster-details.component';
import { PoolsComponent } from './polls/pools.component';
import { RemovePoolComponent } from './polls/remove-pool/remove-pool.component';
import { TemplatesService } from './resourses/templates/templates.service';
import { UsersComponent } from './settings/users/users.component';
import { UsersService } from './settings/users/users.service';
/*  -----------------------------------   material   --------------------------------------*/

import { onError } from 'apollo-link-error';
import { InMemoryCache } from 'apollo-cache-inmemory';
import { environment } from 'src/environments/environment';

@NgModule({
  declarations: [
    AppComponent,
    MainMenuComponent,
    TableComponentComponent,
    ErrorsComponent,
    PoolAddComponent,
    BaSelect,
    FocusMeDirective,
    TableIntoComponent,
    NodesComponent,
    ClustersComponent,
    ClusterDetailsComponent,
    ControllersComponent,
    AddControllerComponent,
    DatapoolsComponent,
    FooterComponent,
    NodeDetailsComponent,
    PoolDetailsComponent,
    PoolsComponent,
    RemoveControllerComponent,
    RemovePoolComponent,
    TemplatesComponent,
    VmsComponent,
    UsersComponent,
    AddUserComponent,
    AddVMStaticPoolComponent,
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
    ReactiveFormsModule,
    FormsModule,
    MatDialogModule,
    MatSelectModule
  ],
  entryComponents: [
    PoolAddComponent,
    AddControllerComponent,
    RemoveControllerComponent,
    RemovePoolComponent,
    AddUserComponent,
    AddVMStaticPoolComponent
  ],
  providers: 
            [
              PoolsService,
              { provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: { hasBackdrop: true, restoreFocus: true } },
              {provide: ErrorStateMatcher, useClass:ShowOnDirtyErrorStateMatcher},
              NodesService,
              ClustersService,
              ControllersService,
              DatapoolsService,
              TemplatesService,
              VmsService,
              UsersService,
              ErrorsService,
              WaitService
            ],
  bootstrap: [AppComponent]
})


export class AppModule {
  

  constructor( private apollo: Apollo,
               private httpLink: HttpLink,
               private errorService: ErrorsService,
               private waitService: WaitService) {

    library.add(faDesktop,faDatabase,faLayerGroup,faPlusCircle,faMinusCircle,faSpinner,faServer,faCog,faChevronUp,faTimesCircle,faFolderOpen,faStar,faTv,faSyncAlt,faBuilding,faTrashAlt,faUsers,faMeh,faChartBar); // Неиспользуемые иконки при финальной сборке удаляются

    const uri = environment.url;
    const link = this.httpLink.create({ uri, includeQuery: true, includeExtensions: false });

    const errorLink = onError(({ graphQLErrors, networkError }) => {
      if (graphQLErrors) {
        graphQLErrors.map(({ message, locations, path }) =>
        console.log(`[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`,));
      }
       
      if (networkError) {
        this.errorService.setError(networkError['error']['errors']);
        this.waitService.setWait(false);
      }
    });

    this.apollo.create({
      link: errorLink.concat(link),
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
          errorPolicy: 'all'
        }
      }
    });
  }
}

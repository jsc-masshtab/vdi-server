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
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { GraphQLModule } from './graphql.module';
import { HttpClientModule } from '@angular/common/http';



/*  -----------------------------------   icons   --------------------------------------*/
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faDesktop,faDatabase,faBuilding, faLayerGroup,faPlusCircle,faSpinner,faServer,faCog,faChevronUp,faTimesCircle,faFolderOpen,faStar,faMinusCircle, faTv,faSyncAlt,faTrashAlt,faUsers,faMeh} from '@fortawesome/free-solid-svg-icons';
//import { faMeh   } from '@fortawesome/free-regular-svg-icons';
/*  -----------------------------------   icons   --------------------------------------*/


import { MainMenuComponent } from './main-menu/main-menu.component';
import { BaSelect } from './common/baSelect';


import { TableComponentComponent } from './common/table-component/table-component.component';
import { BreadcrumbsComponent } from './common/breadcrumbs/breadcrumbs.component';
import { PoolAddComponent } from './polls/pool-add/pool-add.component';
import { PoolsService } from './polls/pools.service';
import { FocusMeDirective } from './common/directives/focusMe.directive';
import { TableIntoComponent } from './common/table-into-component/table-into';
import { NodesComponent } from './resourses/nodes/nodes.component';
import { NodesService } from './resourses/nodes/nodes.service';



/*  -----------------------------------   material   --------------------------------------*/
import { MAT_DIALOG_DEFAULT_OPTIONS } from '@angular/material';
import { MatDialogModule } from '@angular/material/dialog';
import { AddControllerComponent } from './settings/controllers/add-controller/add-controller.component';
import { ControllersService } from './settings/controllers/controllers.service';
import { FooterComponent } from './footer/footer.component';
import { ClusterDetailsComponent } from './resourses/clusters/cluster-details/cluster-details.component';
import { PoolsComponent } from './polls/pools.component';
import { RemovePoolComponent } from './polls/remove-pool/remove-pool.component';
import { TemplatesService } from './resourses/templates/templates.service';
import { TableService } from './common/table-component/table-component.service';
import { UsersComponent } from './settings/users/users.component';
import { UsersService } from './settings/users/users.service';
/*  -----------------------------------   material   --------------------------------------*/



@NgModule({
  declarations: [
    AppComponent,
    MainMenuComponent,
    TableComponentComponent,
    BreadcrumbsComponent,
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
    AddUserComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    GraphQLModule,
    HttpClientModule,
    FontAwesomeModule,
    ReactiveFormsModule,
    FormsModule,
    MatDialogModule
  ],
  entryComponents: [
    PoolAddComponent,
    AddControllerComponent,
    RemoveControllerComponent,
    RemovePoolComponent,
    AddUserComponent
  ],
  providers: 
            [
              PoolsService,
              { provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: { hasBackdrop: true, restoreFocus: true } },
              NodesService,
              ClustersService,
              ControllersService,
              DatapoolsService,
              TemplatesService,
              VmsService,
              TableService,
              UsersService
              
            ],
  bootstrap: [AppComponent]
})


export class AppModule {
  constructor() { 
    library.add(faDesktop,faDatabase,faLayerGroup,faPlusCircle,faMinusCircle,faSpinner,faServer,faCog,faChevronUp,faTimesCircle,faFolderOpen,faStar,faTv,faSyncAlt,faBuilding,faTrashAlt,faUsers,faMeh
      ); // Неиспользуемые иконки при финальной сборке удаляются
  }


}

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSelectModule } from '@angular/material/select';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { AppRoutingModule } from '../../app-routing.module';
import { SharedModule } from '@shared/shared.module';
import { ClustersModule } from '../resourses/clusters/clusters.module';
import { DatapoolsModule } from '../resourses/datapools/datapools.module';
import { NodesModule } from '../resourses/nodes/nodes.module';
import { ResourcePoolsModule } from '../resourses/resource_pools/resource_pools.module';
import { TemplatesModule } from '../resourses/templates/templates.module';
import { VmsModule } from '../resourses/vms/vms.module';
import { AddControllerComponent } from './add-controller/add-controller.component';
import { ControllersComponent } from './all-controllers/controllers.component';
import { ControllersService } from './all-controllers/controllers.service';
import { ControllerDetailsComponent } from './controller-details/controller-details.component';
import { ControllerEventsComponent } from './controller-details/controller-events/controller-events.component';
import { RemoveControllerComponent } from './remove-controller/remove-controller.component';

@NgModule({
  declarations: [
    ControllersComponent,
    AddControllerComponent,
    RemoveControllerComponent,
    ControllerDetailsComponent,
    ControllerEventsComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    AppRoutingModule,
    MatDialogModule,
    MatSelectModule,
    ReactiveFormsModule,
    MatCheckboxModule,
    ClustersModule,
    ResourcePoolsModule,
    NodesModule,
    DatapoolsModule,
    VmsModule,
    TemplatesModule
  ],
  providers: [ControllersService],
  exports: [
    ControllersComponent,
    ControllerDetailsComponent
  ]
})
export class ControllersModule { }

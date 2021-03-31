import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import { ControllersService } from './all-controllers/controllers.service';
import { ControllersComponent } from './all-controllers/controllers.component';

import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AddControllerComponent } from './add-controller/add-controller.component';
import { RemoveControllerComponent } from './remove-controller/remove-controller.component';
import { ReactiveFormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { ControllerDetailsComponent } from './controller-details/controller-details.component';
import { NodesModule } from '../../resourses/nodes/nodes.module';
import { DatapoolsModule } from '../../resourses/datapools/datapools.module';
import { VmsModule } from '../../resourses/vms/vms.module';
import { TemplatesModule } from '../../resourses/templates/templates.module';
import { ClustersModule } from '../../resourses/clusters/clusters.module';
import { ResourcePoolsModule } from '../../resourses/resource_pools/resource_pools.module';

@NgModule({
  declarations: [
    ControllersComponent,
    AddControllerComponent,
    RemoveControllerComponent,
    ControllerDetailsComponent
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

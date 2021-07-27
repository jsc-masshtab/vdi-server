import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { SharedModule } from '../../../shared/shared.module';
import { DashboardRoutingModule } from '../../dashboard/dashboard-routing.module';
import { DatapoolsModule } from '../datapools/datapools.module';
import { NodesModule } from '../nodes/nodes.module';
import { TemplatesModule } from '../templates/templates.module';
import { VmsModule } from '../vms/vms.module';
import { ResourcePoolsComponent } from './all-resource_pools/resource_pools.component';
import { ResourcePoolsService } from './all-resource_pools/resource_pools.service';
import { ResourcePoolDetailsComponent } from './resource_pool-details/resource_pool-details.component';


@NgModule({
  declarations: [
    ResourcePoolsComponent,
    ResourcePoolDetailsComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    DashboardRoutingModule,
    NodesModule,
    DatapoolsModule,
    VmsModule,
    TemplatesModule
  ],
  providers: [ResourcePoolsService],
  exports: [
    ResourcePoolsComponent,
    ResourcePoolDetailsComponent
  ]
})
export class ResourcePoolsModule { }

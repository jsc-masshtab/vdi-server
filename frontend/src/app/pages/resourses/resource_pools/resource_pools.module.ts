import { DashboardRoutingModule } from '../../dashboard/dashboard-routing.module';
import { ResourcePoolsService } from './all-resource_pools/resource_pools.service';
import { ResourcePoolsComponent } from './all-resource_pools/resource_pools.component';
import { SharedModule } from '../../../shared/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResourcePoolDetailsComponent } from './resource_pool-details/resource_pool-details.component';
import { NodesModule } from '../nodes/nodes.module';
import { DatapoolsModule } from '../datapools/datapools.module';
import { VmsModule } from '../vms/vms.module';
import { TemplatesModule } from '../templates/templates.module';


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

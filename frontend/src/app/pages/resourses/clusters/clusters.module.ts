import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { SharedModule } from '../../../shared/shared.module';
import { DashboardRoutingModule } from '../../dashboard/dashboard-routing.module';
import { DatapoolsModule } from '../datapools/datapools.module';
import { NodesModule } from '../nodes/nodes.module';
import { ResourcePoolsModule} from '../resource_pools/resource_pools.module';
import { TemplatesModule } from '../templates/templates.module';
import { VmsModule } from '../vms/vms.module';
import { ClustersComponent } from './all-clusters/clusters.component';
import { ClustersService } from './all-clusters/clusters.service';
import { ClusterDetailsComponent } from './cluster-details/cluster-details.component';


@NgModule({
  declarations: [
    ClustersComponent,
    ClusterDetailsComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    DashboardRoutingModule,
    ResourcePoolsModule,
    NodesModule,
    DatapoolsModule,
    VmsModule,
    TemplatesModule
  ],
  providers: [ClustersService],
  exports: [
    ClustersComponent,
    ClusterDetailsComponent
  ]
})
export class ClustersModule { }

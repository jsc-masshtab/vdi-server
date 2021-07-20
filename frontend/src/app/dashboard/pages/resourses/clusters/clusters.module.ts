import { DashboardRoutingModule } from '../../../dashboard-routing.module';
import { ClustersService } from './all-clusters/clusters.service';
import { ClustersComponent } from './all-clusters/clusters.component';
import { SharedModule } from '../../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ClusterDetailsComponent } from './cluster-details/cluster-details.component';
import { ResourcePoolsModule} from '../resource_pools/resource_pools.module';
import { NodesModule } from '../nodes/nodes.module';
import { DatapoolsModule } from '../datapools/datapools.module';
import { VmsModule } from '../vms/vms.module';
import { TemplatesModule } from '../templates/templates.module';


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

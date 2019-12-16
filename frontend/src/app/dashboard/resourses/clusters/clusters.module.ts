import { DashboardRoutingModule } from './../../dashboard-routing.module';
import { ClustersService } from './all-clusters/clusters.service';
import { ClustersComponent } from './all-clusters/clusters.component';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
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
    DashboardRoutingModule
  ],
  providers: [ClustersService],
  exports: [
    ClustersComponent,
    ClusterDetailsComponent
  ]
})
export class ClustersModule { }

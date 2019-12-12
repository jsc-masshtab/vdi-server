import { ClustersService } from './all-clusters/clusters.service';
import { ClustersComponent } from './all-clusters/clusters.component';
import { AppRoutingModule } from '../../../app-routing.module';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
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
    BrowserAnimationsModule,
    AppRoutingModule
  ],
  providers: [ClustersService],
  exports: [
    ClustersComponent,
    ClusterDetailsComponent
  ]
})
export class ClustersModule { }

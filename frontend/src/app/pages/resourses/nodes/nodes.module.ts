import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../../shared/shared.module';
import { DatapoolsModule } from '../datapools/datapools.module';
import { TemplatesModule } from '../templates/templates.module';
import { VmsModule } from '../vms/vms.module';
import { NodesComponent } from './all-nodes/nodes.component';
import { NodesService } from './all-nodes/nodes.service';
import { NodeDetailsComponent } from './node-details/node-details.component';


@NgModule({
  declarations: [
    NodesComponent,
    NodeDetailsComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    AppRoutingModule,
    DatapoolsModule,
    VmsModule,
    TemplatesModule
  ],
  providers: [NodesService],
  exports: [
    NodesComponent,
    NodeDetailsComponent
  ]
})
export class NodesModule { }


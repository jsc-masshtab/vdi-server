import { NodeDetailsComponent } from './node-details/node-details.component';
import { AppRoutingModule } from '../../app-routing.module';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { SharedModule } from '../../common/components/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NodesComponent } from './all-nodes/nodes.component';
import { NodesService } from './all-nodes/nodes.service';



@NgModule({
  declarations: [
    NodesComponent,
    NodeDetailsComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    BrowserAnimationsModule,
    AppRoutingModule
  ],
  providers: [NodesService],
  exports: [
    NodesComponent,
    NodeDetailsComponent
  ]
})
export class NodesModule { }

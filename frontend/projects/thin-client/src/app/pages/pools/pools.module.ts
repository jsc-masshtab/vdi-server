import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';


import { PoolDetailsComponent } from './pool-details/pool-details.component';
import { PoolsComponent } from './all-pools/pools.component';
import { AppRoutingModule } from '../../app-routing.module';
import { PoolsService } from './pools.service';
import { RemoteComponent } from './pool-details/remote-component/remote-component';
import { ManageVmComponent } from './pool-details/manage-vm/manage-vm.component';
import { SharedModule } from '@app/shared/shared.module';
import { ButtonRefreshComponent } from '../../components/button-refresh/button-refresh.component';
import { YesNoFormModule } from '../../components/yes-no-form/yes-no-form.module';


@NgModule({
  declarations: [  
    PoolsComponent,
    PoolDetailsComponent,
    RemoteComponent,
    ManageVmComponent,
    ButtonRefreshComponent
    ],
  imports: [
    CommonModule,
    SharedModule,
    YesNoFormModule,
    FontAwesomeModule,
    FormsModule,
    ReactiveFormsModule,
    AppRoutingModule,
    MatSelectModule,
    MatDialogModule
  ],
  providers: [
    PoolsService,
  ],
  exports: [
    PoolsComponent,
    PoolDetailsComponent
  ]
})
export class PoolsModule { }




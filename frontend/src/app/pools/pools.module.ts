import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import { AppRoutingModule } from './../app-routing.module';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ReactiveFormsModule } from '@angular/forms';
import { SharedModule } from './../common/components/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { RemoveUserVmComponent } from './pool-details/vm-details-popup/remove-user/remove-user.component';
import { AddUserVmComponent } from './pool-details/vm-details-popup/add-user/add-user.component';
import { AddVMStaticPoolComponent } from './pool-details/add-vms/add-vms.component';
import { AddUsersPoolComponent } from './pool-details/add-users/add-users.component';
import { PoolAddComponent } from './add-pool/add-pool.component';
import { AddPoolService } from './add-pool/add-pool.service';
import { PoolsService } from './all-pools/pools.service';
import { PoolDetailsService } from './pool-details/pool-details.service';
import { PoolsComponent } from './all-pools/pools.component';
import { PoolDetailsComponent } from './pool-details/pool-details.component';
import { RemoveUsersPoolComponent } from './pool-details/remove-users/remove-users.component';
import { RemoveVMStaticPoolComponent } from './pool-details/remove-vms/remove-vms.component';
import { RemovePoolComponent } from './pool-details/remove-pool/remove-pool.component';
import { VmDetalsPopupComponent } from './pool-details/vm-details-popup/vm-details-popup.component';

@NgModule({
  declarations: [
    PoolsComponent,
    PoolAddComponent,
    PoolDetailsComponent,
    AddUsersPoolComponent,
    RemoveUsersPoolComponent,
    AddVMStaticPoolComponent,
    RemoveVMStaticPoolComponent,
    RemovePoolComponent,
    VmDetalsPopupComponent,
    AddUserVmComponent,
    RemoveUserVmComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    ReactiveFormsModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    MatDialogModule,
    MatSelectModule
  ],
  providers: [
    PoolsService,
    PoolDetailsService,
    AddPoolService
  ],
  entryComponents: [
    PoolAddComponent,
    AddUsersPoolComponent,
    RemoveUsersPoolComponent,
    AddVMStaticPoolComponent,
    RemoveVMStaticPoolComponent,
    RemovePoolComponent,
    VmDetalsPopupComponent,
    AddUserVmComponent,
    RemoveUserVmComponent
  ],
  exports: [
    PoolsComponent,
    PoolDetailsComponent
  ]
})
export class PoolsModule { }

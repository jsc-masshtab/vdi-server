import { PoolsUpdateService } from './all-pools/pools.update.service';
import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import { AppRoutingModule } from '../../app-routing.module';
import { ReactiveFormsModule } from '@angular/forms';
import { SharedModule } from '../common/shared.module';
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

import {MatCheckboxModule, MAT_CHECKBOX_CLICK_ACTION} from '@angular/material/checkbox';
import { RemoveRoleComponent } from './pool-details/remove-role/remove-role.component';
import { RemoveGroupComponent } from './pool-details/remove-group/remove-group.component';
import { AddRoleComponent } from './pool-details/add-role/add-role.component';
import { AddGropComponent } from './pool-details/add-group/add-group.component';

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
    RemoveUserVmComponent,
    RemoveRoleComponent,
    RemoveGroupComponent,
    AddGropComponent,
    AddRoleComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    ReactiveFormsModule,
    AppRoutingModule,
    MatDialogModule,
    MatSelectModule,
    MatCheckboxModule
  ],
  providers: [
    PoolsService,
    PoolDetailsService,
    AddPoolService,
    {provide: MAT_CHECKBOX_CLICK_ACTION, useValue: 'check'},
    PoolsUpdateService
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
    RemoveUserVmComponent,
    RemoveRoleComponent,
    RemoveGroupComponent,
    AddGropComponent,
    AddRoleComponent
  ],
  exports: [
    PoolsComponent,
    PoolDetailsComponent
  ]
})
export class PoolsModule { }

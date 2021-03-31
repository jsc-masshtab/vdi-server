import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import { AppRoutingModule } from '../../app-routing.module';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
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

import { MatCheckboxModule, MAT_CHECKBOX_DEFAULT_OPTIONS, MatCheckboxDefaultOptions } from '@angular/material/checkbox';
import { RemoveGroupComponent } from './pool-details/remove-group/remove-group.component';
import { AddGropComponent } from './pool-details/add-group/add-group.component';
import { PrepareVmPoolComponent } from './pool-details/prepare-vm/prepare-vm.component';
import { EventsModule } from '../log/events/events.module';
import { InfoBackupComponent } from './pool-details/vm-details-popup/info-backup/info-backup.component';

@NgModule({
  declarations: [
    PoolsComponent,
    PoolAddComponent,
    PoolDetailsComponent,
    AddUsersPoolComponent,
    RemoveUsersPoolComponent,
    AddVMStaticPoolComponent,
    PrepareVmPoolComponent,
    RemoveVMStaticPoolComponent,
    RemovePoolComponent,
    VmDetalsPopupComponent,
    AddUserVmComponent,
    RemoveUserVmComponent,
    RemoveGroupComponent,
    AddGropComponent,
    InfoBackupComponent,
  ],
  imports: [
    SharedModule,
    CommonModule,
    EventsModule,
    FontAwesomeModule,
    FormsModule,
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
    {
      provide: MAT_CHECKBOX_DEFAULT_OPTIONS,
      useValue: { clickAction: 'check' } as MatCheckboxDefaultOptions
    }
  ],
  exports: [
    PoolsComponent,
    PoolDetailsComponent
  ]
})
export class PoolsModule { }

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatCheckboxModule, MAT_CHECKBOX_DEFAULT_OPTIONS, MatCheckboxDefaultOptions } from '@angular/material/checkbox';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSelectModule } from '@angular/material/select';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { AppRoutingModule } from '../../app-routing.module';
import { SharedModule } from '../../shared/shared.module';
import { EventsModule } from '../log/events/events.module';
import { PoolAddComponent } from './add-pool/add-pool.component';
import { AddPoolService } from './add-pool/add-pool.service';
import { PoolsComponent } from './all-pools/pools.component';
import { PoolsService } from './all-pools/pools.service';
import { AddGropComponent } from './pool-details/add-group/add-group.component';
import { AddUsersPoolComponent } from './pool-details/add-users/add-users.component';
import { AddVMStaticPoolComponent } from './pool-details/add-vms/add-vms.component';
import { PoolDetailsComponent } from './pool-details/pool-details.component';
import { PoolDetailsService } from './pool-details/pool-details.service';
import { PrepareVmPoolComponent } from './pool-details/prepare-vm/prepare-vm.component';
import { RemoveGroupComponent } from './pool-details/remove-group/remove-group.component';
import { RemovePoolComponent } from './pool-details/remove-pool/remove-pool.component';
import { RemoveUsersPoolComponent } from './pool-details/remove-users/remove-users.component';
import { RemoveVMStaticPoolComponent } from './pool-details/remove-vms/remove-vms.component';
import { AddUserVmComponent } from './pool-details/vm-details-popup/add-user/add-user.component';
import { ConvertToTemaplteComponent } from './pool-details/vm-details-popup/convert-to-template/convert-to-template.component';
import { InfoBackupComponent } from './pool-details/vm-details-popup/info-backup/info-backup.component';
import { RemoveUserVmComponent } from './pool-details/vm-details-popup/remove-user/remove-user.component';
import { SpiceComponent } from './pool-details/vm-details-popup/spice/spice.component';
import { VmDetalsPopupComponent } from './pool-details/vm-details-popup/vm-details-popup.component';
import { VmDetailsPopupService } from './pool-details/vm-details-popup/vm-details-popup.service';

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
    SpiceComponent,
    ConvertToTemaplteComponent
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
    VmDetailsPopupService,
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

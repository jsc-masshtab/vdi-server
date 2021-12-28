import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import {MatMenuModule} from '@angular/material/menu'; 

import { PoolDetailsComponent } from './pool-details/pool-details.component';
import { PoolsComponent } from './all-pools/pools.component';
import { AppRoutingModule } from '../../app-routing.module';
import { PoolsService } from './pools.service';
import { RemoteComponent } from './pool-details/remote-component/remote-component';
import { ManageVmComponent } from './pool-details/manage-vm/manage-vm.component';
import { SharedModule } from '@app/shared/shared.module';
import { YesNoFormModule } from '../../components/yes-no-form/yes-no-form.module';
import { MessengerComponent } from './pool-details/messenger/messenger.component';
import { RemoteMessengerComponent } from './pool-details/remote-messenger/remote-messenger.component';


@NgModule({
  declarations: [  
    PoolsComponent,
    PoolDetailsComponent,
    RemoteComponent,
    ManageVmComponent,
    MessengerComponent,
    RemoteMessengerComponent
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
    MatDialogModule,
    MatMenuModule
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




import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import { ControllersService } from './all-controllers/controllers.service';
import { ControllersComponent } from './all-controllers/controllers.component';

import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AddControllerComponent } from './add-controller/add-controller.component';
import { RemoveControllerComponent } from './remove-controller/remove-controller.component';
import { ReactiveFormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material';



@NgModule({
  declarations: [
    ControllersComponent,
    AddControllerComponent,
    RemoveControllerComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    AppRoutingModule,
    MatDialogModule,
    MatSelectModule,
    ReactiveFormsModule,
    MatCheckboxModule

  ],
  providers: [ControllersService],
  exports: [
    ControllersComponent
  ],
  entryComponents: [
    AddControllerComponent,
    RemoveControllerComponent
  ]
})
export class ControllersModule { }

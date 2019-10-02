import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import { ControllersService } from './all-controllers/controllers.service';
import { ControllersComponent } from './all-controllers/controllers.component';

import { AppRoutingModule } from '../../app-routing.module';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { SharedModule } from '../../common/components/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AddControllerComponent } from './add-controller/add-controller.component';
import { RemoveControllerComponent } from './remove-controller/remove-controller.component';
import { FormsModule } from '@angular/forms';



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
    BrowserAnimationsModule,
    AppRoutingModule,
    MatDialogModule,
    MatSelectModule,
    FormsModule
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

import { AddUserComponent } from './add-auth-directory/add-auth-directory.component';
import { AuthenticationDirectoryComponent } from './all-auth-directory/all-auth-directory.component';
import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { AuthenticationDirectoryService } from './auth-directory.service';

@NgModule({
  declarations: [
    AuthenticationDirectoryComponent,
    AddUserComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    AppRoutingModule,
    MatDialogModule,
    MatSelectModule,
    ReactiveFormsModule
  ],
  providers: [AuthenticationDirectoryService],
  exports: [
    AuthenticationDirectoryComponent
  ],
  entryComponents: [
    AddUserComponent
  ]
})
export class AuthenticationDirectoryModule {}

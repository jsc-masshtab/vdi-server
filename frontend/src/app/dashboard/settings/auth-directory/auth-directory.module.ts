import { AddMappingComponent } from './auth-directory-details/add-mapping/add-mapping.component';
import { AddAuthenticationDirectoryComponent } from './add-auth-directory/add-auth-directory.component';
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
import { MatCheckboxModule } from '@angular/material';
import { AuthenticationDirectoryDetailsComponent } from './auth-directory-details/auth-directory-details.component';
import { RemoveAuthenticationDirectoryComponent } from './auth-directory-details/remove-auth-directory/remove-auth-directory.component';

@NgModule({
   declarations: [
      AuthenticationDirectoryComponent,
      AddAuthenticationDirectoryComponent,
      AuthenticationDirectoryDetailsComponent,
      RemoveAuthenticationDirectoryComponent,
      AddMappingComponent
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
   providers: [
      AuthenticationDirectoryService
   ],
   exports: [
      AuthenticationDirectoryComponent
   ],
   entryComponents: [
      AddAuthenticationDirectoryComponent,
      RemoveAuthenticationDirectoryComponent,
      AddMappingComponent
   ]
})
export class AuthenticationDirectoryModule {}

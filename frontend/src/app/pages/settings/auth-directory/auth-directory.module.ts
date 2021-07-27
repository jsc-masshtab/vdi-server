import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSelectModule } from '@angular/material/select';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../../shared/shared.module';
import { AddAuthenticationDirectoryComponent } from './add-auth-directory/add-auth-directory.component';
import { AuthenticationDirectoryComponent } from './all-auth-directory/all-auth-directory.component';
import { AddGropComponent } from './auth-directory-details/add-group/add-group.component';
import { AddMappingComponent } from './auth-directory-details/add-mapping/add-mapping.component';
import { AuthenticationDirectoryDetailsComponent } from './auth-directory-details/auth-directory-details.component';
import { MappingComponent } from './auth-directory-details/mapping/mapping.component';
import { RemoveAuthenticationDirectoryComponent } from './auth-directory-details/remove-auth-directory/remove-auth-directory.component';
import { RemoveGroupComponent } from './auth-directory-details/remove-group/remove-group.component';
import { SyncGroupComponent } from './auth-directory-details/sync-group/sync-group.component';
import { AuthenticationDirectoryService } from './auth-directory.service';

@NgModule({
   declarations: [
      AuthenticationDirectoryComponent,
      AddAuthenticationDirectoryComponent,
      AuthenticationDirectoryDetailsComponent,
      RemoveAuthenticationDirectoryComponent,
      AddMappingComponent,
      MappingComponent,
      AddGropComponent,
      RemoveGroupComponent,
      SyncGroupComponent
   ],
   imports: [
      SharedModule,
      CommonModule,
      FontAwesomeModule,
      AppRoutingModule,
      MatDialogModule,
      MatSelectModule,
      ReactiveFormsModule,
      MatCheckboxModule,
      FormsModule
   ],
   providers: [
      AuthenticationDirectoryService
   ],
   exports: [
      AuthenticationDirectoryComponent
   ]
})
export class AuthenticationDirectoryModule {}

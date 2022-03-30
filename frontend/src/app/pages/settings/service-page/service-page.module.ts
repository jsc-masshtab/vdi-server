import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatDialogModule } from '@angular/material/dialog';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { SharedModule } from '@app/shared/shared.module';

import { ConfirmModalComponent } from './confirm-modal/confirm-modal.component';
import { ServiceControlsComponent } from './service-controls/service-controls.component';
import { ServicePageComponent } from './service-page.component';
import { ReactiveFormsModule } from '@angular/forms';

@NgModule({
    imports: [
        CommonModule,
        SharedModule,
        FontAwesomeModule,
        MatDialogModule,
        ReactiveFormsModule
    ],
    declarations: [ServicePageComponent, ConfirmModalComponent, ServiceControlsComponent]
})
export class ServicePageModule { }

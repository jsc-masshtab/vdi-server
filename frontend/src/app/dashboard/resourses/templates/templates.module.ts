import { TemplateDetailsComponent } from './template-details/template-details.component';
import { TemplatesService } from './all-templates/templates.service';
import { TemplatesComponent } from './all-templates/templates.component';

import { AppRoutingModule } from '../../../app-routing.module';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';


@NgModule({
  declarations: [
    TemplatesComponent,
    TemplateDetailsComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    BrowserAnimationsModule,
    AppRoutingModule
  ],
  providers: [TemplatesService],
  exports: [
    TemplatesComponent,
    TemplateDetailsComponent
  ]
})
export class TemplatesModule { }

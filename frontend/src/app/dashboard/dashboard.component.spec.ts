import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialog } from '@angular/material/dialog';
import { RouterTestingModule } from '@angular/router/testing';

import { WebsocketService } from '../core/services/websock.service';
import { DashboardComponent } from './dashboard.component';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;

  let dialogStub: Partial<MatDialog>;
  let wsStub: Partial<WebsocketService>;

  beforeEach(waitForAsync(() => {
    wsStub = {
      init() {}
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ DashboardComponent ],
      providers: [
        {
          provide: MatDialog,
          useValue: dialogStub
        },
        {
          provide: WebsocketService,
          useValue: wsStub
        },
      ],
      schemas: [ CUSTOM_ELEMENTS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

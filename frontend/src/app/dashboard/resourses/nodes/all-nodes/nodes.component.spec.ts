import { NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { NodesComponent } from './nodes.component';
import { NodesService } from './nodes.service';

describe('NodesComponent', () => {
  let component: NodesComponent;
  let fixture: ComponentFixture<NodesComponent>;

  let serviceStub: Partial<NodesService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getAllNodes(): any {
        return {
          valueChanges: of({
            data: {
              nodes: []
            }
          })
        };
      },
      paramsForGetNodes: {
        spin: false
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ NodesComponent ],
      providers: [
        {
          provide: NodesService,
          useValue: serviceStub
        },
      ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NodesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
